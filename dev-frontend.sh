#!/bin/bash

# =============================================================================
# Sample Multi Agent RAG LLM Chatbot - Frontend Development Script
# =============================================================================
# This script starts only the frontend service for development
# =============================================================================

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

echo "================================"
echo "⚛️  Frontend Development Mode"
echo "================================"

cd frontend

# Check if Node.js is installed
if ! command -v node >/dev/null 2>&1; then
    echo "Error: Node.js is not installed"
    exit 1
fi

print_status "Node.js version: $(node --version)"
print_status "npm version: $(npm --version)"

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    print_status "Installing dependencies..."
    npm install
fi

print_success "Frontend setup complete!"
echo ""
print_status "Starting React development server..."
print_status "Frontend will be available at: http://localhost:3000"
print_status "Press Ctrl+C to stop"
echo ""

# Start the development server
npm start