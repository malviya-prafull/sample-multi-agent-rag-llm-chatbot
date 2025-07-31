#!/bin/bash

# Navigate to the backend directory
cd "$(dirname "$0")"

# Parse command line arguments
SETUP_ONLY=false
if [ "$1" = "--setup-only" ]; then
    SETUP_ONLY=true
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate the virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies from requirements.txt..."
pip install -r requirements.txt

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "Warning: .env file not found. Creating template..."
    echo "NVIDIA_API_KEY=your_nvidia_api_key_here" > .env
    echo "Please add your NVIDIA API key to backend/.env file"
fi

# Setup the database and vector store
echo "Setting up the database and vector store..."
python data_script.py

# Only start server if not in setup-only mode
if [ "$SETUP_ONLY" = false ]; then
    # Run the FastAPI application
    echo "Starting FastAPI server..."
    ./venv/bin/python3.13 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
else
    echo "Backend setup complete! Server not started (setup-only mode)."
fi
