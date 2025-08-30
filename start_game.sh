#!/bin/bash

# Script to launch Scrabbot in local test mode

set -e

WORKDIR="/workspaces/scrabbot"
WEB_DIR="$WORKDIR/build/web"
WEB_PORT=8080

echo "🎮 Scrabbot - Game startup"
echo "================================"

# Verify we are in the correct directory
cd "$WORKDIR"

# Create web directory if it doesn't exist
mkdir -p "$WEB_DIR"

# Verify that web interface exists
if [ ! -f "$WEB_DIR/index.html" ]; then
    echo "❌ Web interface missing in $WEB_DIR/index.html"
    exit 1
fi

# Function to clean up background processes
cleanup() {
    echo ""
    echo "🧹 Cleaning up processes..."

    # Kill web server if it exists
    if [ ! -z "$WEB_PID" ]; then
        kill $WEB_PID 2>/dev/null || true
        echo "   Web server stopped"
    fi

    # Kill other Python servers on port 8080
    pkill -f "python.*http.server.*8080" 2>/dev/null || true

    echo "✅ Cleanup completed"
    exit 0
}

# Configure cleanup on interruption
trap cleanup SIGINT SIGTERM

# Check if port is already in use
if lsof -i:$WEB_PORT >/dev/null 2>&1; then
    echo "⚠️  Port $WEB_PORT already in use, attempting to stop processes..."
    pkill -f "python.*http.server.*$WEB_PORT" 2>/dev/null || true
    sleep 2
fi

# Start web server in background
echo "🌐 Starting web server on port $WEB_PORT..."
cd "$WEB_DIR"
python3 -m http.server $WEB_PORT > /dev/null 2>&1 &
WEB_PID=$!

# Wait for server to start
sleep 2

# Verify that server is working
if ! curl -s http://localhost:$WEB_PORT >/dev/null; then
    echo "❌ Unable to start web server"
    cleanup
fi

echo "✅ Web server started (PID: $WEB_PID)"
echo "🔗 Interface available at: http://localhost:$WEB_PORT"

# Return to working directory
cd "$WORKDIR"

# Configure environment for bot
export GODOT_WEB_URL="http://localhost:$WEB_PORT"
export TELEGRAM_BOT_TOKEN="test-token"

echo ""
echo "🤖 Starting bot test..."
echo "==============================="

# Launch bot test
python3 test_local.py

# Cleanup will be called automatically at the end
