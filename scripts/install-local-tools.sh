#!/usr/bin/env bash
# Creates the off-repo local_tools tree. Never writes into the git workspace.
set -euo pipefail

ROOT="${HOME}/local_tools"
ADAPTERS="${ROOT}/mcp_adapters"
OLLAMA="${ROOT}/ollama"
CLONE="${HOME}/github/ixamal/ix"
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

mkdir -p "${ADAPTERS}" "${OLLAMA}" "${HOME}/github/ixamal"

if [[ ! -e "${CLONE}" ]]; then
  ln -s "${REPO_ROOT}" "${CLONE}"
  echo "Linked ${CLONE} -> ${REPO_ROOT}"
elif [[ -L "${CLONE}" ]]; then
  echo "Clone path already linked: ${CLONE} -> $(readlink "${CLONE}")"
else
  echo "Clone path exists: ${CLONE}"
fi

# Copy adapter templates only if the destination is empty of our stubs.
for stub in ableton.py dj_bridge.js houdini.py README.md; do
  src="${REPO_ROOT}/schemas/adapters/${stub}"
  dst="${ADAPTERS}/${stub}"
  if [[ -f "${src}" && ! -e "${dst}" ]]; then
    cp "${src}" "${dst}"
    echo "Installed adapter stub ${dst}"
  fi
done

if [[ ! -f "${OLLAMA}/README.md" ]]; then
  cat > "${OLLAMA}/README.md" <<'EOF'
# Ollama lives here — outside git

Install the official Ollama binary with their installer, then point it at loopback:

    export OLLAMA_HOST=127.0.0.1:11434
    export OLLAMA_MODELS="${HOME}/local_tools/ollama/models"

Do not copy weights or the binary into ~/github/ixamal/ix.
In Cursor: Settings → Models → OpenAI-compatible base URL http://127.0.0.1:11434/v1
EOF
  echo "Wrote ${OLLAMA}/README.md"
fi

MCP_EXAMPLE="${REPO_ROOT}/schemas/mcp.example.json"
MCP_TARGET="${HOME}/.cursor/mcp.json"
mkdir -p "${HOME}/.cursor"
if [[ -f "${MCP_EXAMPLE}" && ! -e "${MCP_TARGET}" ]]; then
  cp "${MCP_EXAMPLE}" "${MCP_TARGET}"
  echo "Wrote ${MCP_TARGET} from the public example. Edit locally; never commit it."
elif [[ -e "${MCP_TARGET}" ]]; then
  echo "Left existing ${MCP_TARGET} untouched."
fi

echo
echo "Off-repo layout:"
echo "  ${ROOT}"
echo "  ${ADAPTERS}"
echo "  ${OLLAMA}"
echo "  ${CLONE}"
echo "  ${MCP_TARGET}"
echo
echo "Ollama is NOT installed by this script. Install it yourself, then bind 127.0.0.1."
