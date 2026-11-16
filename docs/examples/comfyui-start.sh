#!/usr/bin/env bash
# Start ComfyUI (LaunchAgent), wait for HTTP, open the UI. No comfy launch/stop.
set -euo pipefail

UID_N="$(id -u)"
LABEL="gui/${UID_N}/ai.ixamal.comfyui"
URL="http://127.0.0.1:8188"

launchctl kickstart -k "$LABEL" 2>/dev/null || launchctl kickstart "$LABEL"

for _ in $(seq 1 60); do
  if curl -sf -o /dev/null --max-time 2 "$URL/"; then
    echo "ComfyUI up at $URL"
    open "$URL"
    exit 0
  fi
  sleep 2
done

echo "ComfyUI did not answer on $URL — see ~/local_tools/comfyui/comfyui.log" >&2
exit 1
