import socket
import network
import urequests

from machine import Pin, PWM
from utime import sleep

from music import melody
from notes import notes
from config import buzzer_pin, button_pin, led_pin, wifi_ssid, wifi_password, ntfy_topic, udp_port, udp_message

buzzer = PWM(Pin(buzzer_pin))   # pin where buzzer is connected
# pin where you may connect a button
button = Pin(button_pin, Pin.IN, Pin.PULL_UP)
led = Pin(led_pin, Pin.OUT)

track = 1      # choose track here (see the list in melodies.py)
volume = 600   # set volume to a value between 0 and 1000


def playtone(frequency):
    buzzer.duty_u16(volume)
    buzzer.freq(frequency)


def be_quiet():
    buzzer.duty_u16(0)  # turns sound off


def duration(tempo, t):
    # calculate the duration of a whole note in milliseconds (60s/tempo)*4 beats
    wholenote = (60000 / tempo) * 4

    # calculate the duration of the current note
    # (we need an integer without decimals, hence the // instead of /)
    if t > 0:
        note_duration = wholenote // t
    elif (t < 0):
        # dotted notes are represented with negative durations
        note_duration = wholenote // abs(t)
        note_duration *= 1.5  # increase their duration by a half

    return note_duration


def playsong(mysong):
    try:
        print(mysong[0])  # print title of the song to the shell
        tempo = mysong[1]  # get the tempo for this song from the melodies list

        # iterate over the notes of the melody.
        # The array is twice the number of notes (notes + durations)
        for note in range(2, len(mysong), 2):
            note_duration = duration(tempo, int(mysong[note+1]))

            if (mysong[note] == "REST"):
                be_quiet()
            else:
                playtone(notes[mysong[note]])

            # we only play the note for 90% of the duration...
            sleep(note_duration*0.9/1000)
            be_quiet()
            # ... and leave 10% as a pause between notes
            sleep(note_duration*0.1/1000)

    except:
        be_quiet()


wlan = None


def send_notification(topic, message):
    global wlan

    if not wlan:
        print('No internet access')
        return

    if not wlan.isconnected():
        print(f'Wlan isnt connected. status: {wlan.status()}')
        return

    urequests.post(f'http://ntfy.sh/{topic}', data=message)


try:
    if wifi_ssid and wifi_password:
        print(f'Connecting to "{wifi_ssid}"')
        wlan = network.WLAN(network.STA_IF)
        wlan.disconnect()
        wlan.active(False)
        sleep(1)
        wlan.active(True)
        wlan.connect(wifi_ssid, wifi_password)
        print('Ok!')
except Exception as e:
    print('Error conectando al wifi:', e)

# network.STAT_IDLE: 0
# network.STAT_CONNECTING: 1
# network.STAT_WRONG_PASSWORD: -3
# network.STAT_NO_AP_FOUND: -2
# network.STAT_CONNECT_FAIL: -1

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

while True:
    led.on()
    if button.value() == 0:
        led.off()
        print("Timbre")
        try:
            sock.sendto(udp_message, ('255.255.255.255', udp_port))
        except Exception as e:
            print('Error sending udp message:', e)
        send_notification(ntfy_topic, 'Hay alguien en la puerta')
        playsong(melody[track])

        while button.value() == 0:
            sleep(0.1)
    sleep(0.05)
