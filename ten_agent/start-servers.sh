#!/bin/bash

echo "🚀 Starting Therapist TEN Agent backend servers..."

# Source environment variables
if [ -f /app/.env ]; then
    source /app/.env
    echo "✅ Environment variables loaded"
else
    echo "⚠️  Warning: .env file not found"
fi

# Start API server in background
echo "🔄 Starting API server on port ${SERVER_PORT:-8080}..."
cd /app
HOST=0.0.0.0 PORT=${SERVER_PORT:-8080} ./bin/ten_agent &
API_PID=$!
echo "✅ API server started (PID: $API_PID)"

# Start Graph Designer server in background
echo "🔄 Starting Graph Designer server on port ${GRAPH_DESIGNER_SERVER_PORT:-49483}..."
tman designer &
DESIGNER_PID=$!
echo "✅ Graph Designer server started (PID: $DESIGNER_PID)"

# Wait for servers to start
sleep 3

# Check if servers are running
if ps -p $API_PID > /dev/null; then
    echo "✅ API server is running"
else
    echo "❌ API server failed to start"
fi

if ps -p $DESIGNER_PID > /dev/null; then
    echo "✅ Graph Designer server is running"
else
    echo "❌ Graph Designer server failed to start"
fi

echo "🎉 Therapist Agent backend servers startup complete!"
echo "📡 API server: http://localhost:${SERVER_PORT:-8080}"
echo "🎨 Graph Designer: http://localhost:${GRAPH_DESIGNER_SERVER_PORT:-49483}"
echo ""
echo "💡 Container will remain running. Use 'docker exec -it therapist_agent_dev bash' for interactive access."

# Keep container running
tail -f /dev/null