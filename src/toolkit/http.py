import socket
from uasyncio import open_connection


async def request(host, path, port=80, method='GET', headers=None, body=None):
    if headers is None:
        headers = {}

    addr = socket.getaddrinfo(host, port)[0][-1]
    reader, writer = await open_connection(addr[0], addr[1])

    if body is None:
        body_bytes = b""
    elif isinstance(body, bytes):
        body_bytes = body
    else:
        body_bytes = str(body).encode()

    if "Host" not in headers:
        headers["Host"] = host

    if body_bytes:
        headers["Content-Length"] = str(len(body_bytes))

    request_lines = [f"{method} {path} HTTP/1.0"]
    for k, v in headers.items():
        request_lines.append(f"{k}: {v}")

    request_lines.append("")
    request_data = "\r\n".join(request_lines).encode()

    writer.write(request_data + b"\r\n")

    if body_bytes:
        writer.write(body_bytes)

    await writer.drain()

    response = b""
    while True:
        chunk = await reader.read(256)
        if not chunk:
            break
        response += chunk

    writer.close()
    await writer.wait_closed()

    return response
