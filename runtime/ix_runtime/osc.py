"""Minimal OSC 1.0 encoder/decoder. Stdlib only."""

from __future__ import annotations

import struct
from typing import Any


def _pad(data: bytes) -> bytes:
    padding = (4 - (len(data) % 4)) % 4
    return data + (b"\x00" * padding)


def encode_string(value: str) -> bytes:
    return _pad(value.encode("utf-8") + b"\x00")


def encode_message(address: str, *args: Any) -> bytes:
    tags = [","]
    payload = b""
    for arg in args:
        if isinstance(arg, bool):
            tags.append("T" if arg else "F")
        elif isinstance(arg, int):
            tags.append("i")
            payload += struct.pack(">i", arg)
        elif isinstance(arg, float):
            tags.append("f")
            payload += struct.pack(">f", arg)
        elif isinstance(arg, str):
            tags.append("s")
            payload += encode_string(arg)
        else:
            raise TypeError(f"Unsupported OSC arg: {type(arg)!r}")
    return encode_string(address) + encode_string("".join(tags)) + payload


def _read_string(buffer: bytes, offset: int) -> tuple[str, int]:
    end = buffer.index(b"\x00", offset)
    value = buffer[offset:end].decode("utf-8")
    end += 1
    end += (4 - (end % 4)) % 4
    return value, end


def decode_message(buffer: bytes) -> tuple[str, list[Any]]:
    address, offset = _read_string(buffer, 0)
    tags, offset = _read_string(buffer, offset)
    if not tags.startswith(","):
        raise ValueError("OSC type tag string must start with ','")
    args: list[Any] = []
    for tag in tags[1:]:
        if tag == "i":
            (value,) = struct.unpack(">i", buffer[offset : offset + 4])
            args.append(value)
            offset += 4
        elif tag == "f":
            (value,) = struct.unpack(">f", buffer[offset : offset + 4])
            args.append(float(value))
            offset += 4
        elif tag == "s":
            value, offset = _read_string(buffer, offset)
            args.append(value)
        elif tag == "T":
            args.append(True)
        elif tag == "F":
            args.append(False)
        else:
            raise ValueError(f"Unsupported OSC tag '{tag}'")
    return address, args
