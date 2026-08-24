#!/usr/bin/env python3
"""Houdini MCP stub. Live copy: ~/local_tools/mcp_adapters/houdini.py"""

from __future__ import annotations

import os
import sys

HOST = os.environ.get("HOUDINI_MCP_HOST", "127.0.0.1")


def main() -> int:
    if HOST not in {"127.0.0.1", "localhost"}:
        raise SystemExit(f"Refusing non-loopback host {HOST}")
    print("houdini stub — keep hou sockets on 127.0.0.1", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
