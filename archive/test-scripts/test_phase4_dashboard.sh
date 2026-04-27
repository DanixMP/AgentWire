#!/bin/bash

# Phase 4 Test Script
# This script starts both the backend and frontend for testing

echo "🚀 Starting AgentWire Phase 4 Test"
echo "=================================="
echo ""

# Check if uvicorn is available
if ! command -v uvicorn &> /dev/null; then
    echo "❌ uvicorn not found. Please install: pip install uvicorn"
    exit 1
fi

# Check if npm is available
if ! command -v npm &> /dev/null; then
    echo "❌ npm not found. Please install Node.js"
    exit 1
fi

echo "✓ Prerequisites check passed"
echo ""

# Start backend in background
echo "📡 Starting AgentWire backend on port 8000..."
uvicorn agentwire.bus:app --reload --port 8000 &
BACKEND_PID=$!
echo "   Backend PID: $BACKEND_PID"

# Wait for backend to start
sleep 3

# Start frontend
echo ""
echo "🎨 Starting dashboard on port 5173..."
echo ""
cd dashboard && npm run dev

# Cleanup on exit
trap "echo ''; echo '🛑 Stopping servers...'; kill $BACKEND_PID 2>/dev/null; exit" INT TERM EXIT
