#!/bin/bash
# 5am play harvest. Load with docs/examples/ai.ixamal.crate-favorites.plist
set -euo pipefail
cd "${HOME}/github/ixamal/ix"
export PYTHONPATH=crate
python3 -m ix_crate favorites --execute --playlists
