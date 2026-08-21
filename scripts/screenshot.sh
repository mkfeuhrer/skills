#!/usr/bin/env bash
# Render an HTML artifact to PNG using the local playwright chromium build.
# Usage: scripts/screenshot.sh <file.html> [out.png] [width] [height]
set -euo pipefail
SRC="$(cd "$(dirname "$1")" && pwd)/$(basename "$1")"
OUT="${2:-${SRC%.html}.png}"
W="${3:-1440}"
H="${4:-2400}"
BIN=$(find ~/Library/Caches/ms-playwright -path "*chrome-headless-shell-mac*/chrome-headless-shell" | sort | tail -1)
[ -n "$BIN" ] || { echo "chrome-headless-shell not found; install playwright browsers"; exit 1; }
"$BIN" --headless --disable-gpu \
  --screenshot="$OUT" --window-size=${W},${H} --virtual-time-budget=4000 "file://$SRC" >/dev/null 2>&1
echo "Wrote $OUT"
