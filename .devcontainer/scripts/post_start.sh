#!/usr/bin/env bash
set -euo pipefail

if [ -d "/workspaces/scrabbot/.venv" ]; then
    source /workspaces/scrabbot/.venv/bin/activate || true
fi

# Validate Godot install and print version
if command -v godot >/dev/null 2>&1; then
    echo "Godot version:" $(godot --version)
else
    echo "Godot not found in PATH" >&2
fi

echo "Post-start completed."


