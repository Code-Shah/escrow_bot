from flask import Flask, jsonify
from threading import Thread
import logging
from waitress import serve
import time
import requests
import socket
from collections import deque

# Configure logging for the keep-alive server
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger('keep_alive')

app = Flask(__name__)
_used_ports = deque(maxlen=5)  # Keep track of recently used ports

@app.route('/')
def home():
    return jsonify({"status": "healthy", "message": "Bot is alive!"})

@app.route('/health')
def health():
    return jsonify({"status": "ok", "timestamp": time.time()})

def find_available_port(start_port=8282, max_attempts=100):
    """Find an available port starting from start_port"""
    for port in range(start_port, start_port + max_attempts):
        # Skip recently used ports
        if port in _used_ports:
            continue

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('0.0.0.0', port))
                _used_ports.append(port)
                return port
            except OSError:
                continue
    raise RuntimeError(f"No available ports found between {start_port} and {start_port + max_attempts - 1}")

def run(port=None):
    """Start the Flask server using waitress"""
    try:
        if port is None:
            port = find_available_port()

        logger.info(f"Starting keep-alive server on port {port}")
        serve(app, host='0.0.0.0', port=port, threads=2)
    except Exception as e:
        logger.error(f"Error in keep-alive server: {str(e)}")
        # Don't raise the exception, as this is a background service

def monitor(port):
    """Monitor the health endpoint"""
    while True:
        try:
            response = requests.get(f'http://localhost:{port}/health')
            if response.status_code != 200:
                logger.warning("Health check failed")
            time.sleep(30)  # Check every 30 seconds
        except Exception as e:
            logger.error(f"Health check error: {str(e)}")
            time.sleep(5)  # Shorter retry interval on error

def keep_alive():
    """Creates and starts a web server that will keep the bot alive"""
    try:
        # Find an available port
        port = find_available_port()

        # Start the server in a separate thread
        server_thread = Thread(target=run, args=(port,), daemon=True)
        server_thread.start()
        logger.info("Keep-alive server thread started successfully")

        # Start the monitoring in a separate thread
        monitor_thread = Thread(target=monitor, args=(port,), daemon=True)
        monitor_thread.start()
        logger.info("Health monitoring thread started successfully")

    except Exception as e:
        logger.error(f"Failed to start keep-alive server: {str(e)}")
        # Don't raise the exception, allow the bot to continue without keep-alive
        logger.warning("Bot will continue without keep-alive functionality")