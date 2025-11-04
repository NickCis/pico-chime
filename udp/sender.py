import socket
import time

BROADCAST_IP = "255.255.255.255"   # UDP broadcast address
PORT = 5005                        # Arbitrary port
MESSAGE = b"DOORBELL_PRESSED"

def send_broadcast():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    while True:
        input("Press Enter to 'ring' the doorbell...")
        sock.sendto(MESSAGE, (BROADCAST_IP, PORT))
        print("Doorbell broadcast sent!")

if __name__ == "__main__":
    send_broadcast()
