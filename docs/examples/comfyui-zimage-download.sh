#!/usr/bin/env bash
# One job: finish Z-Image Turbo weights for the browser template (resume curl).
set -euo pipefail
M="$HOME/local_tools/comfyui/ComfyUI/models"
LOG="$HOME/local_tools/comfyui/reports/zimage-download-$(date -u +%Y%m%dT%H%M%SZ).log"
exec >>"$LOG" 2>&1
echo "=== zimage download $(date) ==="

dl() {
  local url="$1" dest="$2"
  mkdir -p "$(dirname "$dest")"
  echo "GET $dest"
  curl -fL --retry 10 --retry-delay 5 -C - -o "${dest}.partial" "$url"
  mv "${dest}.partial" "$dest"
  ls -lh "$dest"
}

dl "https://huggingface.co/Comfy-Org/z_image_turbo/resolve/main/split_files/text_encoders/qwen_3_4b.safetensors" \
  "$M/text_encoders/qwen_3_4b.safetensors"

dl "https://huggingface.co/Comfy-Org/z_image_turbo/resolve/main/split_files/diffusion_models/z_image_turbo_bf16.safetensors" \
  "$M/diffusion_models/z_image_turbo_bf16.safetensors"

echo "=== done $(date) ==="
