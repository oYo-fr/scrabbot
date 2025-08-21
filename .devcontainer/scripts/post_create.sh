#!/usr/bin/env bash
set -euo pipefail

# Create and activate venv for the workspace
if [ ! -d "/workspaces/scrabbot/.venv" ]; then
    python3 -m venv /workspaces/scrabbot/.venv
fi

source /workspaces/scrabbot/.venv/bin/activate || true

python -m ensurepip --upgrade || true
python -m pip install --upgrade pip setuptools wheel

# Install project Python dependencies
if [ -f "/workspaces/scrabbot/bot/requirements.txt" ]; then
    python -m pip install -r /workspaces/scrabbot/bot/requirements.txt
fi

# Install SQLite3 for database management
sudo apt update && sudo apt install -y sqlite3 || true

# Ensure Git is configured minimally (useful inside containers)
git config --global init.defaultBranch main || true
git config --global pull.rebase false || true

echo "Python environment ready."

# Build Godot targets sequentially (Linux, Windows, Web)
cd /workspaces/scrabbot
echo "Running Godot exports..."
bash scripts/export_godot.sh "Linux/X11" "godot" "build/linux/scrabbot.x86_64" || true
bash scripts/export_godot.sh "Windows Desktop" "godot" "build/windows/Scrabbot.exe" || true
bash scripts/export_godot.sh "Web" "godot" "../docs/miniapp/game/index.html" || true

echo "Post-create completed."
