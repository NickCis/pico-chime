import utime
import errno
import socket
import uasyncio
from machine import Pin

from toolkit.config import config
from toolkit.http import request

from music import Player
from songs import songs

button = None


async def send_broadcast():
    udp_port = config['chime']['udp_port']
    udp_message = config['chime']['udp_message'].encode('utf8')
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.setblocking(False)

    for _ in range(3):
        try:
            sock.sendto(udp_message, ('255.255.255.255', udp_port))
        except OSError as e:
            if e.args[0] == errno.EAGAIN:
                await uasyncio.sleep_ms(10)
                continue
            else:
                print('[doorbell] errno:',
                      errno.errorcode.get(e.errno, e.errno), e)
        except Exception as e:
            print('[doorbell] Error sending udp message:', e)

        break

    try:
        sock.close()
    except:
        pass


async def send_notification(message):
    try:
        topic = config['chime']['ntfy_topic']
        await request('ntfy.sh', path=f'/{topic}', method='POST', body=message)
    except Exception as e:
        print('[doorbell] Error sending ntfy notification:', e)


async def coroutine():
    global button
    button_pin = config['chime']['button_pin']
    button = Pin(button_pin, Pin.IN, Pin.PULL_UP)
    wait_time = config['chime']['pressed_ms']
    buzzer_pin = config['chime']['buzzer_pin']
    player = Player(pin=buzzer_pin)

    while True:
        if button.value() == 0:
            pressed = utime.ticks_ms()
            while button.value() == 0 and (utime.ticks_ms() - pressed) < wait_time:
                await uasyncio.sleep_ms(20)

            if (utime.ticks_ms() - pressed) >= wait_time:
                print('[doorbell] time pressed (ms)', utime.ticks_ms() - pressed)
                try:
                    song = songs[config['chime']['track']]
                    uasyncio.create_task(player.playsong(song))
                except Exception as e:
                    print('[doorbell] error playing', e)

                await send_broadcast()
                await send_notification('Hay alguien en la puerta')

                while button.value() == 0:
                    await uasyncio.sleep(1)
            else:
                print('[doorbell] button ignored (debounced)')

        await uasyncio.sleep_ms(50)
