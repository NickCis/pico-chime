import uasyncio
from machine import Pin

from toolkit import wifi
from toolkit import clock
from toolkit import config
# from toolkit import server
from toolkit import telnet

import doorbell

initial = {
    'clock': {
        'sync': True,
        'delta': -3,
    },
    'ap': {
        'ssid': 'Chime',
    },
    'server': {
        'enabled': True,
        'port': 80,
    },
    'chime': {
        'buzzer_pin': 0,
        'button_pin': 2,
        'led_pin': 'LED',
        'ntfy_topic': '',
        'udp_port': 5005,
        'udp_message': 'DOORBELL_PRESSED',
        'track': 1,
        'pressed_ms': 500,
    }
}


async def main():
    config.init(initial=initial)

    uasyncio.create_task(wifi.coroutine())
    uasyncio.create_task(clock.coroutine())
    # uasyncio.create_task(server.coroutine())
    uasyncio.create_task(telnet.coroutine())
    uasyncio.create_task(doorbell.coroutine())

    led_pin = config.config['chime']['led_pin']
    led = Pin(led_pin, Pin.OUT)

    while True:
        if doorbell.button and doorbell.button.value() == 0:
            led.off()
        else:
            led.on()
        await uasyncio.sleep_ms(50)

# Start event loop and run entry point coroutine
uasyncio.run(main())
