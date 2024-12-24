import socket
from system import System
import atexit

def start_e_stop_server(host: str, port: int, system: System):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen(1)
    print(f"Server started on {host}:{port}")
    running = True

    def on_exit():
        running = False
        server.close()
        print("Server stopped")

    atexit.register(on_exit)

    while running:
        conn, addr = server.accept()
        print(f"Connection from {addr}")
        while True:
            data = conn.recv(1024)
            if not data:
                break
            data = data.decode()
            print(f"Received: {data}")
            if data == "stop":
                print('Stopping system')
                system.Q.clear()
                system.stop()
        conn.close()