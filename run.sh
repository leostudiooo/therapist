#!/bin/bash

# AI Therapist Voice Chat - Startup Script

echo "🧠 Starting AI Therapist Voice Chat System..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ .env file not found. Please copy .env.example to .env and fill in your API keys."
    exit 1
fi

# Start backend server
echo "🚀 Starting CSM AI Therapist backend server..."
cd backend
export NO_TORCH_COMPILE=1
export TOKENIZERS_PARALLELISM=false
uv sync --frozen
echo "🔧 Starting backend server..."
uv run uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
cd ..

# Wait for backend to start and test health
echo "⏳ Waiting for backend to initialize..."
sleep 8

# Test backend health
echo "🔍 Testing backend health..."
for i in {1..10}; do
    if curl -s http://localhost:8000/health > /dev/null; then
        echo "✅ Backend is healthy!"
        break
    else
        echo "⏳ Backend not ready yet (attempt $i/10)..."
        sleep 2
    fi
done

# Start frontend server
echo "🎨 Starting Next.js frontend server..."
cd frontend
npm install
npm run dev &
FRONTEND_PID=$!
cd ..

echo "✅ Both servers are starting up!"
echo "🌐 Frontend: http://localhost:3000"
echo "🔧 Backend API: http://localhost:8000"
echo "📊 Backend Health: http://localhost:8000/health"
echo ""
echo "Press Ctrl+C to stop both servers"

# Function to cleanup on exit
cleanup() {
    echo "🛑 Stopping servers..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    exit 0
}

# Set trap to cleanup on script exit
trap cleanup SIGINT SIGTERM

# Wait for either process to finish
wait