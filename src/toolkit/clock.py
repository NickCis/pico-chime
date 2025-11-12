# https://docs.micropython.org/en/latest/library/machine.RTC.html
# https://github.com/micropython/micropython/blob/master/docs/esp8266/quickref.rst#real-time-clock-rtc

import time
import errno
import socket
import struct
import machine
import uasyncio

from .wifi import wlan
from .config import config

wait_time = 60 * 60  # 60 mins
host = "pool.ntp.org"
timeout = 2


async def get_ntp_time():
    '''Inspired from https://github.com/micropython/micropython-lib/blob/master/micropython/net/ntptime/ntptime.py'''
    ntp_query = bytearray(48)
    ntp_query[0] = 0x1B
    addr = socket.getaddrinfo(host, 123)[0][-1]
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setblocking(False)

    try:
        s.settimeout(timeout)
        s.sendto(ntp_query, addr)
        while True:
            try:
                msg = s.recv(48)
                break
            except OSError as e:
                err = e.args[0]
                if err == errno.EAGAIN:
                    await uasyncio.sleep_ms(500)
                    continue
                raise e
    finally:
        s.close()

    val = struct.unpack("!I", msg[40:44])[0]

    # 2024-01-01 00:00:00 converted to an NTP timestamp
    MIN_NTP_TIMESTAMP = 3913056000

    # Y2036 fix
    #
    # The NTP timestamp has a 32-bit count of seconds, which will wrap back
    # to zero on 7 Feb 2036 at 06:28:16.
    #
    # We know that this software was written during 2024 (or later).
    # So we know that timestamps less than MIN_NTP_TIMESTAMP are impossible.
    # So if the timestamp is less than MIN_NTP_TIMESTAMP, that probably means
    # that the NTP time wrapped at 2^32 seconds.  (Or someone set the wrong
    # time on their NTP server, but we can't really do anything about that).
    #
    # So in that case, we need to add in those extra 2^32 seconds, to get the
    # correct timestamp.
    #
    # This means that this code will work until the year 2160.  More precisely,
    # this code will not work after 7th Feb 2160 at 06:28:15.
    #
    if val < MIN_NTP_TIMESTAMP:
        val += 0x100000000

    # Convert timestamp from NTP format to our internal format

    epoch_year = time.gmtime(0)[0]
    if epoch_year == 2000:
        # (date(2000, 1, 1) - date(1900, 1, 1)).days * 24*60*60
        ntp_delta = 3155673600
    elif epoch_year == 1970:
        # (date(1970, 1, 1) - date(1900, 1, 1)).days * 24*60*60
        ntp_delta = 2208988800
    else:
        raise Exception("Unsupported epoch: {}".format(epoch_year))

    return val - ntp_delta


async def get_auto_time():
    # https://ipapi.co/utc_offset -> '-0300'
    raise Exception('Auto timezone not implemented')


async def coroutine():
    rtc = machine.RTC()

    while True:
        if not wlan or not wlan.isconnected():
            await uasyncio.sleep(30)
            continue

        try:
            if config['clock']['sync']:
                delta = int(config['clock']['delta'])
                t = await get_ntp_time()
                tm = time.gmtime(t)
                rtc.datetime((tm[0], tm[1], tm[2], tm[6] + 1,
                             tm[3] + delta, tm[4], tm[5], 0))
                print('[clock] time synced successfully')
            await uasyncio.sleep(wait_time)
        except Exception as e:
            print('[clock] time sync failed', e)
            await uasyncio.sleep(60)
