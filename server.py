#!/usr/bin/env python3
from flask import Flask, request, jsonify, send_file
import os
import datetime
import subprocess
import threading
import json

app = Flask(__name__)

# Connected targets ka record
connected = []

@app.route('/')
def home():
    return '''
    <!DOCTYPE html>
    <html>
    <head><title>Custom Server Active</title></head>
    <body style="font-family: monospace; background: #0a0a0a; color: #0f0; padding: 20px;">
        <h2>🔥 Custom Server Running</h2>
        <p>Status: <span style="color: #0f0;">● ONLINE</span></p>
        <p>Time: {}</p>
        <hr>
        <p>📡 Endpoints:</p>
        <ul>
            <li><b>GET /ping</b> - Health check (for Uptime Robot)</li>
            <li><b>GET /status</b> - Server status</li>
            <li><b>POST /api/data</b> - Receive data from target</li>
        </ul>
    </body>
    </html>
    '''.format(datetime.datetime.now())

@app.route('/ping')
def ping():
    '''Uptime Robot ke liye'''
    return 'OK', 200

@app.route('/status')
def status():
    return jsonify({
        'status': 'online',
        'time': str(datetime.datetime.now()),
        'connected': len(connected),
        'port': os.environ.get('PORT', 8080)
    })

@app.route('/api/data', methods=['POST', 'GET'])
def receive():
    '''Target se data aayega yahan'''
    if request.method == 'POST':
        data = request.get_data()
        client = request.remote_addr
        
        # Log kar
        print(f"[{datetime.datetime.now()}] Data from {client}: {len(data)} bytes")
        
        # Save kar
        with open(f'log_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.txt', 'wb') as f:
            f.write(data)
        
        # Client ko record kar
        if client not in connected:
            connected.append(client)
        
        return 'Received', 200
    
    return jsonify({'message': 'Send POST request with data'})

# Health check for Render
@app.route('/health')
def health():
    return 'OK', 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    print(f"""
    ╔══════════════════════════════════╗
    ║   🚀 SERVER STARTED              ║
    ║   Port: {port}                    ║
    ║   Time: {datetime.datetime.now()} ║
    ╚══════════════════════════════════╝
    """)
    app.run(host='0.0.0.0', port=port)
