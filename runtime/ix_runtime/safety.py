from __future__ import annotations

import json
import re
from typing import Any

ALLOWED_DAW = frozenset({"play", "stop", "set_tempo", "arm_track", "read_tempo"})
ALLOWED_DJ = frozenset({"read_bpm", "read_fader", "read_beat_phase", "read_track_id"})
ALLOWED_UE = frozenset({"set_cache_time", "set_density", "set_emissive", "inspect_level"})
ALLOWED_DCC = frozenset({"inspect_scene", "export_fbx", "list_nodes"})
ALLOWED = {
    "daw": ALLOWED_DAW,
    "dj": ALLOWED_DJ,
    "ue": ALLOWED_UE,
    "dcc": ALLOWED_DCC,
}

MAX_VOLUME_DB = 0.0
LOOPBACK_HOSTS = frozenset({"127.0.0.1", "localhost"})
FORBIDDEN_HOSTS = frozenset({"0.0.0.0", "::", "[::]"})


class SafetyError(PermissionError):
    pass


def assert_loopback_host(host: str) -> str:
    normalized = host.strip().lower()
    if normalized in FORBIDDEN_HOSTS:
        raise SafetyError(f"Refusing to bind {host}. IX sockets listen on 127.0.0.1 only.")
    if normalized not in LOOPBACK_HOSTS:
        raise SafetyError(f"Host '{host}' is not loopback. Bind 127.0.0.1.")
    return "127.0.0.1"


def sanitize_tool_call(family: str, command: str, params: dict[str, Any] | None = None) -> tuple[str, dict[str, Any]]:
    allowed = ALLOWED.get(family)
    if allowed is None:
        raise SafetyError(f"Unknown tool family '{family}'.")
    if command not in allowed:
        raise SafetyError(f"Action '{command}' blocked by the {family} circuit breaker.")
    next_params = dict(params or {})
    volume = next_params.get("volume")
    if isinstance(volume, (int, float)) and volume > MAX_VOLUME_DB:
        next_params["volume"] = MAX_VOLUME_DB
    return command, next_params


def is_public_safe_mcp(config_text: str) -> bool:
    """Reject configs that embed absolute home paths or secrets before a commit."""
    if re.search(r"/Users/[^/\s]+/", config_text):
        return False
    if re.search(r"(api[_-]?key|secret|token)\s*[:=]", config_text, re.I):
        return False
    try:
        data = json.loads(config_text)
    except json.JSONDecodeError:
        return False
    servers = data.get("mcpServers", {})
    if not isinstance(servers, dict):
        return False
    blob = json.dumps(servers)
    return "127.0.0.1" in blob or "${HOME}" in blob or "~/local_tools" in blob
