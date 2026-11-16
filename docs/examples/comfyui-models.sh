#!/usr/bin/env bash
# Download ComfyUI model files from schemas/comfyui-models.manifest.json into
# ~/local_tools/comfyui/ComfyUI/models/. Resumes partial downloads. Verifies sha256
# when the manifest lists one. Uses curl (not Python urllib) for HTTPS on macOS.
#
#   docs/examples/comfyui-models.sh
#   COMFYUI_TIERS=ui-zimage docs/examples/comfyui-models.sh
#   COMFYUI_DETACH=1 docs/examples/comfyui-models.sh
#
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
MANIFEST="${ROOT}/schemas/comfyui-models.manifest.json"
COMFY_ROOT="${COMFYUI_ROOT:-${HOME}/local_tools/comfyui}"
MODELS="${COMFY_ROOT}/ComfyUI/models"
REPORTS="${COMFY_ROOT}/reports"
TIERS="${COMFYUI_TIERS:-all}"
DRY_RUN="${COMFYUI_DRY_RUN:-0}"
DETACH="${COMFYUI_DETACH:-0}"
PYTHON="${COMFYUI_PYTHON:-${HOME}/local_tools/comfyui/.venv/bin/python3}"
[[ -x "$PYTHON" ]] || PYTHON="$(command -v python3)"

for arg in "$@"; do
  case "$arg" in
    -h|--help)
      sed -n '2,12p' "$0" | sed 's/^# \?//'
      exit 0
      ;;
  esac
done

[[ -f "$MANIFEST" ]] || { echo "Missing $MANIFEST" >&2; exit 1; }
mkdir -p "$MODELS" "$REPORTS"

if [[ -z "${HF_TOKEN:-}" && -z "${HUGGING_FACE_HUB_TOKEN:-}" && -f "${HOME}/.cache/huggingface/token" ]]; then
  HF_TOKEN="$(tr -d '[:space:]' < "${HOME}/.cache/huggingface/token")"
  export HF_TOKEN
fi

run_main() {
  export MANIFEST MODELS TIERS DRY_RUN
  export HF_TOKEN="${HF_TOKEN:-${HUGGING_FACE_HUB_TOKEN:-}}"
  "$PYTHON" - <<'PY'
import json, os, subprocess, sys

manifest_path = os.environ["MANIFEST"]
models_root = os.environ["MODELS"]
tiers_wanted = os.environ["TIERS"]
dry = os.environ.get("DRY_RUN") == "1"
hf_token = (os.environ.get("HF_TOKEN") or "").strip()

with open(manifest_path, encoding="utf-8") as f:
    data = json.load(f)

tier_filter = None if tiers_wanted.strip().lower() == "all" else {
    t.strip() for t in tiers_wanted.split(",") if t.strip()
}

def sha256(path):
    import hashlib
    h = hashlib.sha256()
    with open(path, "rb") as bf:
        for chunk in iter(lambda: bf.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def ok_file(path, entry):
    if not os.path.isfile(path):
        return False
    expected = entry.get("sha256")
    if expected:
        return sha256(path) == expected.lower()
    size = entry.get("bytes")
    if size and os.path.getsize(path) < int(size * 0.95):
        return False
    return os.path.getsize(path) > 0

def curl_download(entry_id, url, dest_partial, gated):
    cmd = [
        "curl", "-fL", "--retry", "5", "--retry-delay", "3",
        "--connect-timeout", "30",
        "-C", "-", "-o", dest_partial, url,
    ]
    if hf_token:
        cmd[1:1] = ["-H", f"Authorization: Bearer {hf_token}"]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "").strip()
        if gated and ("401" in err or "403" in err):
            print(
                f"FAIL {entry_id}: gated — accept FLUX license on Hugging Face, then huggingface-cli login",
                file=sys.stderr,
            )
        else:
            print(f"FAIL {entry_id}: curl exit {proc.returncode}\n{err[:500]}", file=sys.stderr)
        return False
    return True

tier_rank = {"ui-zimage": 0, "floor-sdxl": 1, "floor-flux": 2}
indexed = list(enumerate(data["files"]))
if tier_filter:
    indexed = [(i, e) for i, e in indexed if e["tier"] in tier_filter]
indexed.sort(key=lambda pair: (tier_rank.get(pair[1]["tier"], 9), pair[0]))
files = [e for _, e in indexed]

present_ids = set()
errors = 0
for entry in files:
    tier = entry["tier"]
    skip_ref = entry.get("skip_if_present")
    if skip_ref and skip_ref in present_ids:
        print(f"skip {entry['id']} (already have {skip_ref})")
        continue

    dest = os.path.join(models_root, entry["relative_path"])
    os.makedirs(os.path.dirname(dest), exist_ok=True)

    if ok_file(dest, entry):
        print(f"ok   {entry['relative_path']}")
        present_ids.add(entry["id"])
        continue

    url = entry["url"]
    gated = entry.get("gated", False)
    print(f"need {entry['relative_path']} ({tier})", flush=True)
    if dry:
        print(f"     {url}")
        continue

    partial = dest + ".partial"
    if not curl_download(entry["id"], url, partial, gated):
        errors += 1
        continue
    os.replace(partial, dest)

    if not ok_file(dest, entry):
        print(f"WARN {entry['relative_path']}: verify failed (size/sha256)", file=sys.stderr)
        errors += 1
    else:
        print(f"got  {entry['relative_path']}", flush=True)
        present_ids.add(entry["id"])

sys.exit(1 if errors else 0)
PY
}

if [[ "$DETACH" == "1" ]]; then
  LOG="${LOG:-${REPORTS}/comfyui-models-$(date -u +%Y%m%dT%H%M%SZ).log}"
  echo "Logging to $LOG"
  nohup env COMFYUI_DETACH=0 "$0" >>"$LOG" 2>&1 &
  echo "PID $! — tail -f $LOG"
  exit 0
fi

run_main
