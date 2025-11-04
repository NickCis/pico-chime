import socket
import network
import time
from machine import Pin
from wifi_connect import connect_wifi

# --- Configuration ---
SSID = "your_wifi_ssid"
PASSWORD = "your_wifi_password"
BROADCAST_IP = "255.255.255.255"
PORT = 5005
MESSAGE = b"DOORBELL_PRESSED"

# --- Setup Wi-Fi ---
connect_wifi(SSID, PASSWORD)

# --- Setup button ---
button = Pin(15, Pin.IN, Pin.PULL_UP)

# --- Create UDP socket ---
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

print("Ready! Press the button to send a UDP broadcast.")

while True:
    if not button.value():  # Button pressed (assuming active low)
        sock.sendto(MESSAGE, (BROADCAST_IP, PORT))
        print("Doorbell broadcast sent!")
        time.sleep(1)  # Debounce delay
