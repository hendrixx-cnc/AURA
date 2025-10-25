#!/bin/bash
# Helper script to run the WebSocket stress test
# Usage: ./run_stress_test.sh [number_of_users]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Default values
NUM_USERS=${1:-50}
SERVER_PORT=8765

echo "================================================================================"
echo "AURA WebSocket Stress Test Runner"
echo "================================================================================"
echo ""
echo "Configuration:"
echo "  - Number of Users: $NUM_USERS"
echo "  - Server Port: $SERVER_PORT"
echo "  - Project Root: $PROJECT_ROOT"
echo ""

# Check if server is already running
if lsof -Pi :$SERVER_PORT -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo "⚠ Warning: WebSocket server is already running on port $SERVER_PORT"
    echo "Using existing server instance..."
    echo ""
    RUN_SERVER=false
else
    echo "Starting WebSocket server..."
    RUN_SERVER=true
fi

# Function to cleanup on exit
cleanup() {
    if [ "$RUN_SERVER" = true ] && [ ! -z "$SERVER_PID" ]; then
        echo ""
        echo "Stopping WebSocket server (PID: $SERVER_PID)..."
        kill $SERVER_PID 2>/dev/null || true
        wait $SERVER_PID 2>/dev/null || true
        echo "Server stopped."
    fi
}

trap cleanup EXIT INT TERM

# Start server if needed
if [ "$RUN_SERVER" = true ]; then
    cd "$PROJECT_ROOT"
    python3 tests/simple_websocket_server.py &
    SERVER_PID=$!
    echo "Server started (PID: $SERVER_PID)"
    echo "Waiting 2 seconds for server to initialize..."
    sleep 2
    echo ""
fi

# Run stress test
echo "Starting stress test with $NUM_USERS concurrent users..."
echo ""

cd "$PROJECT_ROOT"
python3 tests/stress_test_50_users.py --users $NUM_USERS

echo ""
echo "Stress test completed!"
echo ""
