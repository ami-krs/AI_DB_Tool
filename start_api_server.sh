#!/bin/bash
# Start the FastAPI backend server for AI autocomplete

echo "🚀 Starting AI Database Tool API Server..."
echo "📍 Server will run on http://localhost:8000"
echo ""

cd "$(dirname "$0")"
python webapp/api_server.py


