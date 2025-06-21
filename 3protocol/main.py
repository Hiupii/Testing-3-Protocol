import asyncio
import socket
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from gmqtt import Client as MQTTClient
import os

# Fix asyncio bug on Windows
if os.name == 'nt':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# ========== TCP SERVER ==========
def tcp_server():
    HOST = '0.0.0.0'
    PORT = 8888
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        print(f"[TCP] Listening on port {PORT}...")
        while True:
            conn, addr = s.accept()
            print(f"[TCP] Connected from {addr}")
            threading.Thread(target=handle_tcp_client, args=(conn, addr), daemon=True).start()

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
    server = HTTPServer(('0.0.0.0', 5000), SimpleHandler)
    print("[HTTP] Listening on port 5000...")
    server.serve_forever()

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
    await client.connect('localhost')  # Đổi IP nếu broker không chạy local
    await asyncio.Future()  # Giữ kết nối vĩnh viễn

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
