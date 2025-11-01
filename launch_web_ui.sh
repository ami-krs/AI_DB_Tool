#!/bin/bash
# Launch script for AI Database Tool Web UI

echo "🚀 Launching AI Database Tool Web Interface..."
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from template..."
    cp env.example .env
    echo "✅ Created .env file. Please add your OPENAI_API_KEY to test AI features."
fi

# Launch Streamlit
echo "🌐 Starting Streamlit server..."
echo "📱 The web UI will open at: http://localhost:8501"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

streamlit run webapp/app.py --server.port 8501 --server.address localhost

