#!/bin/bash

# Multimodal RAG System Startup Script

echo "🤖 Starting Multimodal RAG System..."

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

# Create necessary directories
mkdir -p data static

# Try to install dependencies if possible
echo "📦 Checking dependencies..."
python3 -c "import fastapi" 2>/dev/null || {
    echo "⚠️  FastAPI not found. Attempting to install..."
    pip install fastapi uvicorn python-multipart || {
        echo "❌ Failed to install FastAPI. Please install manually:"
        echo "   pip install fastapi uvicorn python-multipart"
        echo ""
        echo "🔄 Starting with basic HTTP server..."
        python3 main.py
        exit 0
    }
}

# Start the FastAPI server
echo "🚀 Starting FastAPI server on http://localhost:8000"
echo "📂 Data will be stored in: ./data/"
echo "🌐 Open http://localhost:8000 in your browser"
echo ""
echo "Press Ctrl+C to stop the server"

python3 -c "
import uvicorn
from main import create_basic_server

app = create_basic_server()
uvicorn.run(app, host='0.0.0.0', port=8000)
" || {
    echo "❌ Failed to start FastAPI server. Starting basic HTTP server..."
    python3 main.py
}