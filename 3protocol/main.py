import asyncio
import socket
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from gmqtt import Client as MQTTClient
import os

# Fix asyncio policy for Windows
if os.name == 'nt':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# ========== TCP SERVER ==========
def tcp_server():
    HOST = '0.0.0.0'
    PORT = 8888
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Cho phép reuse port
    try:
        s.bind((HOST, PORT))
        s.listen()
        print(f"[TCP] Listening on port {PORT}...")
        while True:
            conn, addr = s.accept()
            print(f"[TCP] Connected from {addr}")
            threading.Thread(target=handle_tcp_client, args=(conn, addr), daemon=True).start()
    except OSError as e:
        print(f"[TCP] Port {PORT} error: {e}")

def handle_tcp_client(conn, addr):
    with conn:
        while True:
            data = conn.recv(1024)
            if not data:
                break
            print(f"[TCP] From {addr}: {data.decode().strip()}")

# ========== HTTP SERVER ==========
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        print(f"[HTTP] GET from {self.client_address} Path: {self.path}")
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"GET OK")

    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length)
        print(f"[HTTP] POST from {self.client_address}: {body.decode().strip()}")
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"POST OK")

def http_server():
    HOST, PORT = '0.0.0.0', 5000
    try:
        HTTPServer.allow_reuse_address = True  # Cho phép reuse port
        server = HTTPServer((HOST, PORT), SimpleHandler)
        print(f"[HTTP] Listening on port {PORT}...")
        server.serve_forever()
    except OSError as e:
        print(f"[HTTP] Port {PORT} error: {e}")

# ========== MQTT SUBSCRIBER ==========
TOPIC = 'test/topic'

def on_connect(client, flags, rc, properties):
    print('[MQTT] Connected')
    client.subscribe(TOPIC)

def on_message(client, topic, payload, qos, properties):
    print(f'[MQTT] Received on {topic}: {payload.decode()}')

async def mqtt_subscriber():
    client = MQTTClient("python-subscriber")
    client.on_connect = on_connect
    client.on_message = on_message
    try:
        await client.connect('localhost')  # Đổi IP nếu cần
    except Exception as e:
        print(f"[MQTT] Connection error: {e}")
    await asyncio.Future()

# ========== MAIN ==========
def start_tcp_server():
    threading.Thread(target=tcp_server, daemon=True).start()

def start_http_server():
    threading.Thread(target=http_server, daemon=True).start()

def start_all():
    start_tcp_server()
    start_http_server()
    asyncio.run(mqtt_subscriber())

if __name__ == '__main__':
    start_all()
