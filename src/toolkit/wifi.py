# https://docs.micropython.org/en/latest/library/network.WLAN.html

# Using Both AP and STA interface yields problems while routing requests.
# The easiest solution is to re-compile micropython applying this patch:
#   https://github.com/orgs/micropython/discussions/12903#discussioncomment-7542738

import socket
import network
import uasyncio

from .config import config

wlan = None
ap = None
ap_dns_socket = None
ap_inactivity_timer = None
wait_time = 2 * 60

StatusNames = {
    network.STAT_IDLE: 'STAT_IDLE',
    network.STAT_CONNECTING: 'STAT_CONNECTING',
    network.STAT_WRONG_PASSWORD: 'STAT_WRONG_PASSWORD',
    network.STAT_NO_AP_FOUND: 'STAT_NO_AP_FOUND',
    network.STAT_CONNECT_FAIL: 'STAT_CONNECT_FAIL',
    network.STAT_GOT_IP: 'STAT_GOT_IP',
}

SecurityNames = {
    0: 'OPEN',
    2: 'WEP',
    3: 'WPA-PSK',
    4: 'WPA2-PSK',
    5: 'WPA/WPA2-PSK',
}


def get_state(device):
    if not device:
        return {
            'status': 'NONE',
            'ifconfig': (),
        }

    status = device.status()
    return {
        'status': StatusNames.get(status, status),
        'ifconfig': device.ifconfig(),
    }


def scan():
    global wlan

    if not wlan:
        wlan = network.WLAN(network.STA_IF)
        wlan.active(True)

    networks = []

    for n in wlan.scan():
        networks.append({
            'ssid': n[0].decode('utf8'),
            'channel': n[2],
            'rssi': n[3],
            'security': SecurityNames.get(n[4], n[4]),
            'hidden': n[5] == 1,
        })

    return networks


async def ap_dns_catchall():
    ''' Inspired from https://github.com/pimoroni/phew/blob/main/phew/dns.py '''
    global ap
    global ap_dns_socket

    if ap_dns_socket:
        ap_dns_socket.close()

    ip_address = ap.ifconfig()[0]
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setblocking(False)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(socket.getaddrinfo(ip_address, 53, 0, socket.SOCK_DGRAM)[0][-1])
    ap_dns_socket = sock

    while ap:
        try:
            # yield uasyncio.core._io_queue.queue_read(sock)
            request, client = sock.recvfrom(256)
        except OSError as e:
            err = e.args[0]
            if err == errno.EAGAIN:
                await uasyncio.sleep_ms(500)
                continue
            raise e

        response = request[:2]  # request id
        response += b"\x81\x80"  # response flags
        response += request[4:6] + request[4:6]  # qd/an count
        response += b"\x00\x00\x00\x00"  # ns/ar count
        response += request[12:]  # origional request body
        response += b"\xC0\x0C"  # pointer to domain name at byte 12
        response += b"\x00\x01\x00\x01"  # type and class (A record / IN class)
        response += b"\x00\x00\x00\x3C"  # time to live 60 seconds
        response += b"\x00\x04"  # response length (4 bytes = 1 ipv4 address)
        response += bytes(map(int, ip_address.split(".")))  # ip address parts
        sock.sendto(response, client)


def ap_down():
    global ap
    global ap_dns_socket
    global ap_inactivity_timer

    if ap:
        ap.active(False)
        ap = None

        if ap_dns_socket:
            ap_dns_socket.close()
            ap_dns_socket = None

    get_inactivity_shutdown = None


async def ap_inactivity_shutdown_watch():
    global ap
    global ap_inactivity_timer

    def get_inactivity_shutdown(): return config['ap'].get(
        'inactivity-shutdown', 10 * 60)
    already_running = ap_inactivity_timer != None
    ap_inactivity_timer = get_inactivity_shutdown()

    if already_running:
        return

    while ap and ap_inactivity_timer > 0:
        await uasyncio.sleep(30)

        clients = ap.status('stations')
        if len(clients) > 0:
            ap_inactivity_timer = get_inactivity_shutdown()
        else:
            ap_inactivity_timer = ap_inactivity_timer - 30

    ap_inactivity_timer = None

    if get_inactivity_shutdown() == 0:
        return

    ap_down()


async def ap_reload_config(enabled, ssid, password=None):
    global ap

    if not enabled:
        ap_down()
        return

    if not ap:
        ap = network.WLAN(network.AP_IF)

    ap.config(essid=ssid)

    if password:
        ap.config(password=password)
    else:
        ap.config(security=0)

    ap.active(True)

    while ap.status() == network.STAT_CONNECTING:
        await uasyncio.sleep_ms(500)

    print('[ap] connected successfully', ssid, ap.ifconfig())

    uasyncio.create_task(ap_dns_catchall())
    uasyncio.create_task(ap_inactivity_shutdown_watch())


async def wlan_reload_config(enabled, ssid, password=None):
    global wlan
    print('[wlan] connecting...', enabled, ssid)

    if not enabled:
        if wlan:
            wlan.disconnect()
            wlan.active(False)
            wlan = None
        return

    if not wlan:
        wlan = network.WLAN(network.STA_IF)

    wlan.active(True)
    wlan.connect(ssid, password)

    while wlan.status() == network.STAT_CONNECTING:
        await uasyncio.sleep_ms(500)

    print('[wlan] connected successfully', ssid, wlan.ifconfig())


async def coroutine():
    global wlan

    while True:
        if not ap or ap.status() == network.STAT_IDLE:
            await ap_reload_config(config['ap']['enabled'], config['ap']
                                   ['ssid'], config['ap']['password'])

        if not wlan or wlan.status() == network.STAT_IDLE or wlan.status() == network.STAT_NO_AP_FOUND:
            await wlan_reload_config(config['wlan']['enabled'], config['wlan']
                                     ['ssid'], config['wlan']['password'])
        elif wlan and not wlan.isconnected():
            wlan.disconnect()
            wlan.connect(config['wlan']['ssid'], config['wlan']['password'])

        await uasyncio.sleep(wait_time)
