import socket

PORT = 5005

def listen_broadcast():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("", PORT))  # Bind to all interfaces

    print(f"Listening for UDP broadcasts on port {PORT}...")
    while True:
        data, addr = sock.recvfrom(1024)
        print(f"Received message from {addr}: {data.decode()}")

if __name__ == "__main__":
    listen_broadcast()
