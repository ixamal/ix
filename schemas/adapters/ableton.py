#!/usr/bin/env python3
"""Ableton Live OSC stub. Copy lives in ~/local_tools/mcp_adapters — not in git."""

from __future__ import annotations

import os
import sys

HOST = os.environ.get("ABLETON_OSC_HOST", "127.0.0.1")
PORT = int(os.environ.get("ABLETON_OSC_PORT", "11000"))

ALLOWED = {"play", "stop", "set_tempo", "arm_track", "read_tempo"}
MAX_VOLUME_DB = 0.0


def assert_loopback(host: str) -> None:
    if host not in {"127.0.0.1", "localhost"}:
        raise SystemExit(f"Refusing non-loopback host {host}")


def sanitize(command: str, params: dict) -> tuple[str, dict]:
    if command not in ALLOWED:
        raise PermissionError(f"blocked: {command}")
    if params.get("volume", 0) > MAX_VOLUME_DB:
        params = {**params, "volume": MAX_VOLUME_DB}
    return command, params


def main() -> int:
    assert_loopback(HOST)
    print(f"ableton stub ready on {HOST}:{PORT} (stdio MCP not wired in this stub)", file=sys.stderr)
    print("This stub is a placeholder. Point the real adapter at AbletonOSC.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
