import network
import uasyncio as asyncio
import socket
from machine import Pin
import time

# --- Configuration ---
SSID = "your_wifi_ssid"
PASSWORD = "your_wifi_password"
BROADCAST_IP = "255.255.255.255"
PORT = 5005
MESSAGE = b"DOORBELL_PRESSED"

BUTTON_PIN = 15
LED_PIN = "LED"  # Onboard LED on Pico W

# --- Setup hardware ---
button = Pin(BUTTON_PIN, Pin.IN, Pin.PULL_UP)
led = Pin(LED_PIN, Pin.OUT)

# --- Wi-Fi connection ---
async def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("Connecting to Wi-Fi...")
        wlan.connect(SSID, PASSWORD)
        retries = 0
        while not wlan.isconnected():
            retries += 1
            led.toggle()
            await asyncio.sleep(0.5)
            if retries > 60:  # 30 sec timeout
                print("\nWi-Fi connection timeout, retrying...")
                wlan.disconnect()
                await asyncio.sleep(2)
                wlan.connect(SSID, PASSWORD)
        led.on()
        print("\nConnected to Wi-Fi:", wlan.ifconfig())
    return wlan

# --- Wi-Fi auto-reconnect task ---
async def wifi_monitor(wlan):
    while True:
        if not wlan.isconnected():
            print("Wi-Fi disconnected! Reconnecting...")
            led.off()
            wlan.disconnect()
            await asyncio.sleep(2)
            await connect_wifi()
            led.on()
        await asyncio.sleep(5)

# --- Doorbell broadcast task ---
async def doorbell_sender(wlan):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    print("Doorbell broadcaster ready.")
    print("Press the button to send UDP broadcast.")
    last_state = button.value()

    while True:
        current_state = button.value()
        if current_state == 0 and last_state == 1:  # Falling edge: button pressed
            if wlan.isconnected():
                print("Button pressed! Sending broadcast...")
                sock.sendto(MESSAGE, (BROADCAST_IP, PORT))
                led.off()
                await asyncio.sleep(0.2)
                led.on()
            else:
                print("Button pressed, but Wi-Fi not connected.")
            await asyncio.sleep(0.5)  # Debounce
        last_state = current_state
        await asyncio.sleep(0.05)

# --- Main event loop ---
async def main():
    wlan = await connect_wifi()
    asyncio.create_task(wifi_monitor(wlan))
    await doorbell_sender(wlan)

# --- Run it ---
try:
    asyncio.run(main())
finally:
    asyncio.new_event_loop()

