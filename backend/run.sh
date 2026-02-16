#!/bin/bash
# Development server startup script

set -e

echo "Starting TW Stock Screener Backend..."
echo "======================================="

# Check if .env exists
if [ ! -f .env ]; then
    echo "Error: .env file not found!"
    echo "Please copy .env.example to .env and configure it"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ] && [ ! -d ".venv" ]; then
    echo "Warning: No virtual environment detected"
    echo "Consider creating one: python -m venv venv"
fi

# Run uvicorn server
echo "Starting FastAPI server on http://0.0.0.0:8000"
echo "API Docs: http://localhost:8000/docs"
echo ""

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
