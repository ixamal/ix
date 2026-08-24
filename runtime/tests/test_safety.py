import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ix_runtime.osc import decode_message, encode_message
from ix_runtime.safety import SafetyError, assert_loopback_host, is_public_safe_mcp, sanitize_tool_call


def test_loopback_accepted():
    assert assert_loopback_host("127.0.0.1") == "127.0.0.1"
    assert assert_loopback_host("localhost") == "127.0.0.1"


def test_wan_bind_rejected():
    with pytest.raises(SafetyError):
        assert_loopback_host("0.0.0.0")
    with pytest.raises(SafetyError):
        assert_loopback_host("192.168.1.10")


def test_daw_unknown_command_blocked():
    with pytest.raises(SafetyError):
        sanitize_tool_call("daw", "delete_set", {})


def test_volume_is_capped():
    command, params = sanitize_tool_call("daw", "play", {"volume": 6.0})
    assert command == "play"
    assert params["volume"] == 0.0


def test_osc_roundtrip():
    packet = encode_message("/rekordbox/bpm", 128.0)
    address, args = decode_message(packet)
    assert address == "/rekordbox/bpm"
    assert args[0] == pytest.approx(128.0)


def test_example_mcp_is_commit_safe():
    example = Path(__file__).resolve().parents[2] / "schemas" / "mcp.example.json"
    text = example.read_text(encoding="utf-8")
    assert is_public_safe_mcp(text)
    assert "/Users/" not in text
    assert "0.0.0.0" not in text


def test_mcp_with_home_path_is_not_commit_safe():
    bad = """
    {"mcpServers": {"ableton": {"command": "python", "args": ["/Users/ixamal/secret.py"]}}}
    """
    assert is_public_safe_mcp(bad) is False
