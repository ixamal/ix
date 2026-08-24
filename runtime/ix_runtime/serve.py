"""Loopback OSC + health HTTP. Never binds 0.0.0.0."""

from __future__ import annotations

import argparse
import json
import socket
import struct
import threading
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from .osc import decode_message, encode_message
from .safety import SafetyError, assert_loopback_host

STATE: dict[str, Any] = {
    "host": "127.0.0.1",
    "oscPort": 9000,
    "httpPort": 9100,
    "messages": 0,
    "lastAddress": None,
    "lastArgs": None,
    "updatedAt": None,
}


def forward_to_control_plane(address: str, args: list[Any], control_url: str) -> None:
    payload = json.dumps(
        {"address": address, "args": args, "source": "loopback"}
    ).encode("utf-8")
    request = urllib.request.Request(
        f"{control_url.rstrip('/')}/api/osc/inject",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=1.5) as response:
            response.read()
    except (urllib.error.URLError, TimeoutError, OSError):
        return


def osc_loop(host: str, port: int, control_url: str, stop: threading.Event) -> None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((host, port))
    sock.settimeout(0.5)
    while not stop.is_set():
        try:
            data, _addr = sock.recvfrom(65535)
        except TimeoutError:
            continue
        except OSError:
            break
        try:
            address, args = decode_message(data)
        except (ValueError, struct.error, UnicodeDecodeError):
            continue
        STATE["messages"] += 1
        STATE["lastAddress"] = address
        STATE["lastArgs"] = args
        STATE["updatedAt"] = time.time()
        forward_to_control_plane(address, args, control_url)
    sock.close()


class HealthHandler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
        return

    def do_GET(self) -> None:  # noqa: N802
        if self.path not in ("/health", "/", "/status"):
            self.send_response(404)
            self.end_headers()
            return
        body = json.dumps(STATE).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/send":
            self.send_response(404)
            self.end_headers()
            return
        length = int(self.headers.get("Content-Length", "0"))
        payload = json.loads(self.rfile.read(length) or b"{}")
        address = payload.get("address")
        args = payload.get("args") or []
        if not isinstance(address, str):
            self.send_response(400)
            self.end_headers()
            return
        packet = encode_message(address, *args)
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(packet, (STATE["host"], STATE["oscPort"]))
        sock.close()
        self.send_response(204)
        self.end_headers()


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="IX loopback OSC runtime")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--osc-port", type=int, default=9000)
    parser.add_argument("--http-port", type=int, default=9100)
    parser.add_argument("--control-url", default="http://127.0.0.1:47241")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        host = assert_loopback_host(args.host)
    except SafetyError as error:
        raise SystemExit(str(error)) from error

    STATE["host"] = host
    STATE["oscPort"] = args.osc_port
    STATE["httpPort"] = args.http_port

    stop = threading.Event()
    thread = threading.Thread(
        target=osc_loop,
        args=(host, args.osc_port, args.control_url, stop),
        daemon=True,
    )
    thread.start()
    server = ThreadingHTTPServer((host, args.http_port), HealthHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        stop.set()
        server.shutdown()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
