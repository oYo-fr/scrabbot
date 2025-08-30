#!/usr/bin/env bash
set -euo pipefail

# Create and activate venv for the workspace
if [ ! -d "/workspaces/scrabbot/.venv" ]; then
    python3 -m venv /workspaces/scrabbot/.venv
fi

source /workspaces/scrabbot/.venv/bin/activate || true

python -m ensurepip --upgrade || true
python -m pip install --upgrade pip setuptools wheel

# Install Rust for the vscode user
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y \
    && echo 'source $HOME/.cargo/env' >> ~/.bashrc \
    && source ~/.cargo/env \
    && cargo install wrkflw

# Install project Python dependencies
if [ -f "/workspaces/scrabbot/bot/requirements.txt" ]; then
    python -m pip install -r /workspaces/scrabbot/bot/requirements.txt
fi

# Install Python dependencies for the project
cp bot/requirements.txt /tmp/requirements.txt
pip3 install --user -r /tmp/requirements.txt

# Install SQLite3 for database management
sudo apt update && sudo apt install -y sqlite3 || true

# Ensure Git is configured minimally (useful inside containers)
git config --global init.defaultBranch main || true
git config --global pull.rebase false || true

echo "Python environment ready."

# Install GUT testing framework for Godot
cd /workspaces/scrabbot
echo "Installing GUT testing framework..."
if [ ! -d "godot/addons/gut" ]; then
    mkdir -p godot/addons
    cd godot/addons
    git clone https://github.com/bitwes/Gut.git gut
    cd ../..
    echo "GUT framework installed successfully"
else
    echo "GUT framework already installed"
fi

# Copy test files into Godot project for testing
echo "Setting up Godot test environment..."
mkdir -p godot/tests/dictionaries
if [ -f "tests/dictionaries/test_godot_api.gd" ]; then
    cp tests/dictionaries/test_godot_api.gd godot/tests/dictionaries/
    echo "Godot test files copied"
fi

# Build Godot targets sequentially (Linux, Windows, Web)
echo "Running Godot exports..."
bash scripts/export_godot.sh "Linux/X11" "godot" "build/linux/scrabbot.x86_64" || true
bash scripts/export_godot.sh "Windows Desktop" "godot" "build/windows/Scrabbot.exe" || true
bash scripts/export_godot.sh "Web" "godot" "../docs/miniapp/game/index.html" || true

echo "Post-create completed."
