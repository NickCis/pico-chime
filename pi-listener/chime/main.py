import builtins
from datetime import datetime

from .constants import Port, BuzzerPin, Volume, Song, DoorbellMessage
from .songs import songs
from .music import Player

say = print


def print_date(*args, **kwargs):
    global say
    say(datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], *args, **kwargs)


builtins.print = print_date


def main(port=Port, buzzer_pin=BuzzerPin, volume=Volume, song_name=Song):
    player = Player(pin=buzzer_pin, volume=volume)
    song = songs[0]
    for s in songs:
        if s[0] == song_name:
            song = s
            break

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("", port))  # Bind to all interfaces

    print(f'Listening for UDP broadcasts on port {PORT}...')
    while True:
        data, addr = sock.recvfrom(1024)
        print(f'Received message from {addr}: {data.decode()}')
        if data == DoorbellMessage:
            print(" :: Doorbell")
            player.playsong(song)
