#!/bin/bash

# =============================================================================
# Sample Multi Agent RAG LLM Chatbot - Stop Script
# =============================================================================
# This script stops both backend and frontend services
# =============================================================================

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if port is in use
check_port() {
    if lsof -i:$1 >/dev/null 2>&1; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

# Function to kill processes on specific ports
kill_port() {
    local port=$1
    local service=$2
    
    if check_port $port; then
        print_status "Stopping $service on port $port..."
        local pids=$(lsof -ti:$port)
        if [ ! -z "$pids" ]; then
            echo $pids | xargs kill -TERM >/dev/null 2>&1
            sleep 2
            
            # Force kill if still running
            if check_port $port; then
                print_warning "Force killing $service processes..."
                echo $pids | xargs kill -9 >/dev/null 2>&1
            fi
            
            if ! check_port $port; then
                print_success "$service stopped successfully"
            else
                print_error "Failed to stop $service"
            fi
        fi
    else
        print_status "$service is not running"
    fi
}

echo "================================"
echo "🛑 Stopping Sample Multi Agent RAG LLM Chatbot"
echo "================================"

# Stop backend (port 8000)
kill_port 8000 "Backend"

# Stop frontend (port 3000)
kill_port 3000 "Frontend"

# Clean up log files if they exist
if [ -f "backend.log" ]; then
    print_status "Cleaning up backend.log"
    rm -f backend.log
fi

if [ -f "frontend.log" ]; then
    print_status "Cleaning up frontend.log"
    rm -f frontend.log
fi

print_success "All services stopped successfully"
echo ""
print_status "You can start the application again with: ./start.sh"