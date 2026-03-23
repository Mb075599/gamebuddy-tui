#!/usr/bin/env sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
SCRIPT_PATH="$SCRIPT_DIR/gcii_tui.py"

if command -v python3 >/dev/null 2>&1; then
    exec python3 "$SCRIPT_PATH" "$@"
fi

if command -v python >/dev/null 2>&1; then
    exec python "$SCRIPT_PATH" "$@"
fi

echo "Python was not found in PATH. Install Python 3 and try again." >&2
exit 1
