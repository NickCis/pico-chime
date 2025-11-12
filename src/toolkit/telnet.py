import time
import uasyncio
import builtins

from .config import config

# Telnet bytes and options
IAC = b'\xff'   # 255
DONT = b'\xfe'   # 254
DO = b'\xfd'   # 253
WONT = b'\xfc'   # 252
WILL = b'\xfb'   # 251

# Telnet options
OPT_ECHO = b'\x01'
OPT_SGA = b'\x03'

# Configuration
WELCOME = "MicroPython Pico remote (telnet). Type 'help' for commands.\r\n"
PROMPT = ">>> "

# Keep originals for restoration
original_print = builtins.print

# Global state (single client)
echo_enabled = False
current_writer = None
current_reader = None


def patched_print(*args, **kwargs):
    global current_writer, original_print

    if echo_enabled:
        if current_writer is not None:
            sep = kwargs.get("sep", " ")
            end = kwargs.get("end", "\n")
            msg = sep.join(str(a) for a in args) + end
            msg = msg.replace("\n", "\r\n")

            try:
                current_writer.write(msg.encode())
                try:
                    coro = current_writer.drain()
                    if coro:
                        uasyncio.create_task(coro)
                except:
                    pass
            except:
                pass

    original_print(*args, **kwargs)


def send_iac(writer, cmd, opt):
    try:
        writer.write(IAC + cmd + opt)
    except Exception:
        pass


def negotiate_telnet_options(writer):
    '''
    Minimal telnet negotiation: ask client to stop local echo (server WILL echo)
    and to suppress go-ahead. Many clients will then let server handle echoing.
    '''
    # Tell client: server WILL ECHO (so client should stop locally echoing)
    send_iac(writer, WILL, OPT_ECHO)
    # Tell client: server WILL SUPPRESS GO AHEAD
    send_iac(writer, WILL, OPT_SGA)
    # Optionally: ask the client to DO SUPPRESS GO AHEAD
    send_iac(writer, DO, OPT_SGA)


async def awrite(writer, text):
    '''Simple helper to write text + CRLF'''
    if isinstance(text, str):
        data = text.replace("\n", "\r\n").encode()
    else:
        data = text
    try:
        writer.write(data)
        # small drain to push data
        await writer.drain()
    except Exception:
        pass


# Execute a single command string, capture output and exceptions
def execute_command(cmd, globals_dict):
    """
    Executes command string. Tries eval first (for expressions), then exec.
    Returns a tuple (ok, result_text) where ok is True if executed without raising.
    """
    return (True, 'TODO:\n')


async def read_line_telnet(reader):
    """
    Reads a line from a telnet client, filtering out telnet negotiation
    sequences and returning only normal user-typed bytes.
    Returns a bytes object without CR/LF.
    """
    buf = bytearray()

    while True:
        b = await reader.read(1)
        if not b:
            return b  # disconnected

        # Telnet IAC sequence (interpret as command, not text)
        if b == b'\xff':  # IAC
            # consume next two bytes of negotiation
            opt1 = await reader.read(1)
            opt2 = await reader.read(1)
            # ignore them entirely
            continue

        # CR (carriage return)
        if b == b'\r':
            # consume optional LF
            nxt = await reader.read(1)
            if nxt != b'\n':
                # Put back if not newline (not ideal but ok)
                pass
            return bytes(buf)  # line complete

        # LF alone (rare but handle)
        if b == b'\n':
            return bytes(buf)

        # Append normal bytes
        buf.extend(b)


async def repl_loop(reader, writer):
    '''REPL loop: reads lines, executes them, prints results.'''

    global echo_enabled

    repl_globals = {"__name__": "__telnet__"}
    await awrite(writer, WELCOME)
    await awrite(writer, "Password accepted. Starting remote REPL.\r\nType 'help' for commands, 'exit' to disconnect.\r\n")

    while True:
        try:
            await awrite(writer, PROMPT)
            line = await read_line_telnet(reader)
            await awrite(writer, "\r\n")

            if not line:
                continue

            # decode and strip CRLF and whitespace
            try:
                s = line.decode('utf-8', 'ignore').rstrip('\r\n')
            except Exception:
                s = line.rstrip(b'\r\n').decode('utf-8', 'ignore')
            s_strip = s.strip()
            if not s:
                continue

            # local commands
            if s_strip == "exit" or s_strip == "quit":
                await awrite(writer, "Bye.\r\n")
                break
            elif s_strip == "echo on":
                echo_enabled = True
                await awrite(writer, "On\r\n")
                continue
            elif s_strip == "echo off":
                echo_enabled = False
                await awrite(writer, "Off\r\n")
                continue
            elif s_strip == "time":
                t = time.localtime()
                await awrite(writer, f'{t[0]}-{t[1]:02d}-{t[2]:02d} {t[3]:02d}:{t[4]:02d}:{t[5]:02d}\r\n')
                continue
            elif s_strip == "help":
                help_text = (
                    "Remote telnet commands:\r\n"
                    "  help            - show this help\r\n"
                    "  echo on/off     - enable / disable echoing pico logs\r\n"
                    "  exit/quit       - disconnect\r\n"
                    "You can also enter Python expressions and statements.\r\n"
                )
                await awrite(writer, help_text)
                continue

            # Execute Python
            ok, out = execute_command(s, repl_globals)
            if out:
                # ensure CRLF normalization
                out = out.replace("\n", "\r\n")
                await awrite(writer, out)
            # Finally prompt
        except Exception as e:
            # send error but keep loop running
            try:
                await awrite(writer, "REPL error: {}\r\n".format(e))
            except Exception:
                break


async def handle_client(reader, writer):
    '''Handle one client connection'''
    global current_writer, current_reader, original_print

    password = config['telnet']['password']
    original_print('[telnet] new client')

    try:
        negotiate_telnet_options(writer)
        # short delay so negotiation gets out before prompt
        await uasyncio.sleep_ms(50)

        # Send initial login prompt
        # We'll attempt to avoid echo during password entry by requesting WILL ECHO above.
        await awrite(writer, "Password: ")

        pw_bytes = await read_line_telnet(reader)
        if not pw_bytes:
            original_print('[telnet] no pw bytes disconnect\n')
            # disconnected
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass
            return

        try:
            pw = pw_bytes.decode().strip()
        except Exception:
            pw = str(pw_bytes).strip()

        if pw != password:
            await awrite(writer, "\r\nAuthentication failed.\r\n")
            # small delay then close
            await uasyncio.sleep_ms(50)
            writer.close()
            try:
                await writer.wait_closed()
            except:
                pass
            return

        original_print(f'[telnet] Login correct')
        send_iac(writer, WONT, OPT_ECHO)
        await uasyncio.sleep_ms(50)

        # We only allow one client connected
        if current_writer:
            try:
                current_writer.close()
            except:
                pass

        current_writer = writer
        current_reader = reader

        try:
            builtins.print = patched_print
        except Exception as e:
            original_print(f'[telnet] error {e}')

        await repl_loop(reader, writer)

    except Exception as e:
        original_print('[telnet] handler error:', e)
    finally:
        current_writer = None
        current_reader = None

        try:
            builtins.print = original_print
        except:
            pass

        try:
            writer.close()
            await writer.wait_closed()
        except:
            pass

        original_print('[telnet] Telnet client disconnected')


async def coroutine():
    enabled = config['telnet']['enabled']
    host = config['telnet']['host']
    port = config['telnet']['port']

    if not enabled:
        return

    try:
        print(f'[telnet] Starting telnet server on {host}:{port}')
        server = await uasyncio.start_server(handle_client, host, port)
        await server.wait_closed()
    except Exception as e:
        print('[telnet] error', e)
