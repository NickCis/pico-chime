import errno
import ujson as json

config_file = '/config.json'

config = {
    'clock': {
        'sync': False,
        'delta': 0,
    },
    'ap': {
        'enabled': False,
        'ssid': 'Toolkit',
        'password': '',
        'inactivity-shutdown': 10 * 60,
    },
    'wlan': {
        'enabled': False,
        'ssid': '',
        'password': '',
    },
    'server': {
        'enabled': False,
        'port': 80,
    },
    'telnet': {
        'enabled': False,
        'host': '0.0.0.0',
        'port': 23,
        'password': 'pico',
    },
}


def _update(data):
    for k, v in data.items():
        if type(v) == dict:
            if type(config.get(k, None)) != dict:
                config[k] = {}
            for kk, vv in v.items():
                config[k][kk] = vv
        else:
            config[k] = v


def init(initial={}):
    try:
        _update(initial)
    except Exception as e:
        print('[config] error:', e)

    try:
        with open(config_file) as fd:
            data = json.load(fd)
            _update(data)
    except OSError as e:
        if e.errno != errno.ENOENT:
            print('[config] errno:', errno.errorcode.get(e.errno, e.errno), e)
    except Exception as e:
        print('[config] error:', e)


def update(data):
    try:
        _update(data)
        with open(config_file, 'w') as fd:
            json.dump(config, fd)
    except OSError as e:
        if e.errno != errno.ENOENT:
            print('[config] errno:', errno.errorcode.get(e.errno, e.errno), e)
    except Exception as e:
        print('[config] error:', e)
