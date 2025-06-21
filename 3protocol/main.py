import asyncio
import socket
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from hbmqtt.broker import Broker
from hbmqtt.client import MQTTClient

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
            print(f"[TCP] Connection from {addr}")
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

# ========== MQTT SERVER ==========
broker_config = {
    'listeners': {
        'default': {
            'type': 'tcp',
            'bind': '0.0.0.0:1883',
        }
    },
    'sys_interval': 10,
    'auth': {
        'allow-anonymous': True
    }
}

async def mqtt_broker():
    broker = Broker(broker_config)
    await broker.start()

async def mqtt_subscriber():
    client = MQTTClient()
    await client.connect('mqtt://localhost:1883/')
    await client.subscribe([('test/topic', 0)])
    print("[MQTT] Subscribed to 'test/topic'")
    while True:
        message = await client.deliver_message()
        payload = message.publish_packet.payload.data.decode()
        print(f"[MQTT] Received: {payload}")

# ========== MAIN ==========
def start_tcp_server():
    threading.Thread(target=tcp_server, daemon=True).start()

def start_http_server():
    threading.Thread(target=http_server, daemon=True).start()

def start_mqtt_servers():
    asyncio.run(asyncio.gather(mqtt_broker(), mqtt_subscriber()))

if __name__ == "__main__":
    start_tcp_server()
    start_http_server()
    start_mqtt_servers()
