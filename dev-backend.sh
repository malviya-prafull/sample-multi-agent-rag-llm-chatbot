#!/bin/bash

# =============================================================================
# Sample Multi Agent RAG LLM Chatbot - Backend Development Script
# =============================================================================
# This script starts only the backend service for development
# =============================================================================

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

echo "================================"
echo "🐍 Backend Development Mode"
echo "================================"

cd backend

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    print_status "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
print_status "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
print_status "Installing dependencies..."
pip install -r requirements.txt >/dev/null 2>&1

# Check environment file
if [ ! -f ".env" ]; then
    print_warning ".env file not found. Creating template..."
    echo "NVIDIA_API_KEY=your_nvidia_api_key_here" > .env
    print_warning "Please add your NVIDIA API key to backend/.env file"
fi

# Setup database if needed
if [ ! -f "ecommerce.db" ] || [ ! -d "chroma_db" ]; then
    print_status "Setting up database and vector store..."
    python data_script.py
fi

print_success "Backend setup complete!"
echo ""
print_status "Starting FastAPI development server..."
print_status "Backend will be available at: http://localhost:8000"
print_status "Press Ctrl+C to stop"
echo ""

# Start the server
uvicorn main:app --host 0.0.0.0 --port 8000 --reload