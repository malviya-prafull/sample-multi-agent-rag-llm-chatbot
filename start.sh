#!/bin/bash

# =============================================================================
# Sample Multi Agent RAG LLM Chatbot - Start Script
# =============================================================================
# This script starts both backend and frontend services simultaneously
# =============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to print colored output
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

print_header() {
    echo -e "${PURPLE}================================${NC}"
    echo -e "${PURPLE}$1${NC}"
    echo -e "${PURPLE}================================${NC}"
}

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
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
cleanup_ports() {
    print_status "Cleaning up any existing processes..."
    
    # Kill backend (port 8000)
    if check_port 8000; then
        print_warning "Killing existing backend process on port 8000"
        lsof -ti:8000 | xargs kill -9 >/dev/null 2>&1 || true
    fi
    
    # Kill frontend (port 3000)
    if check_port 3000; then
        print_warning "Killing existing frontend process on port 3000"
        lsof -ti:3000 | xargs kill -9 >/dev/null 2>&1 || true
    fi
}

# Function to setup backend
setup_backend() {
    print_header "Setting up Backend"
    
    cd backend
    
    # Check if Python 3 is installed
    if ! command_exists python3; then
        print_error "Python 3 is not installed. Please install Python 3.13+ and try again."
        exit 1
    fi
    
    print_status "Python version: $(python3 --version)"
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        print_status "Creating virtual environment..."
        python3 -m venv venv
        print_success "Virtual environment created"
    else
        print_status "Virtual environment already exists"
    fi
    
    # Activate virtual environment
    print_status "Activating virtual environment..."
    source venv/bin/activate
    
    # Install dependencies
    print_status "Installing Python dependencies..."
    pip install -r requirements.txt >/dev/null 2>&1
    print_success "Dependencies installed"
    
    # Check if .env file exists
    if [ ! -f ".env" ]; then
        print_warning ".env file not found. Creating template..."
        echo "NVIDIA_API_KEY=your_nvidia_api_key_here" > .env
        print_warning "Please add your NVIDIA API key to backend/.env file"
    fi
    
    # Setup database if needed
    if [ ! -f "ecommerce.db" ] || [ ! -d "chroma_db" ]; then
        print_status "Setting up database and vector store..."
        python data_script.py
        print_success "Database and vector store setup complete"
    else
        print_status "Database and vector store already exist"
    fi
    
    cd ..
}

# Function to setup frontend
setup_frontend() {
    print_header "Setting up Frontend"
    
    cd frontend
    
    # Check if Node.js is installed
    if ! command_exists node; then
        print_error "Node.js is not installed. Please install Node.js 18+ and try again."
        exit 1
    fi
    
    print_status "Node.js version: $(node --version)"
    print_status "npm version: $(npm --version)"
    
    # Install dependencies if node_modules doesn't exist
    if [ ! -d "node_modules" ]; then
        print_status "Installing Node.js dependencies..."
        npm install >/dev/null 2>&1
        print_success "Dependencies installed"
    else
        print_status "Node.js dependencies already installed"
    fi
    
    cd ..
}

# Function to start backend
start_backend() {
    print_status "Starting backend server..."
    cd backend
    source venv/bin/activate
    nohup uvicorn main:app --host 0.0.0.0 --port 8000 --reload > ../backend.log 2>&1 &
    BACKEND_PID=$!
    cd ..
    
    # Wait a moment and check if backend started successfully
    sleep 3
    if kill -0 $BACKEND_PID 2>/dev/null; then
        print_success "Backend started successfully on http://localhost:8000 (PID: $BACKEND_PID)"
    else
        print_error "Failed to start backend. Check backend.log for details."
        exit 1
    fi
}

# Function to start frontend
start_frontend() {
    print_status "Starting frontend server..."
    cd frontend
    
    # Set port to 3000 explicitly
    export PORT=3000
    nohup npm start > ../frontend.log 2>&1 &
    FRONTEND_PID=$!
    cd ..
    
    # Wait a moment and check if frontend started successfully
    sleep 5
    if kill -0 $FRONTEND_PID 2>/dev/null; then
        print_success "Frontend started successfully on http://localhost:3000 (PID: $FRONTEND_PID)"
    else
        print_error "Failed to start frontend. Check frontend.log for details."
        exit 1
    fi
}

# Function to wait for services
wait_for_services() {
    print_header "Waiting for services to be ready"
    
    # Wait for backend
    print_status "Waiting for backend to be ready..."
    for i in {1..30}; do
        if curl -s http://localhost:8000/ >/dev/null 2>&1; then
            print_success "Backend is ready!"
            break
        fi
        if [ $i -eq 30 ]; then
            print_warning "Backend may not be fully ready yet"
        fi
        sleep 2
    done
    
    # Wait for frontend
    print_status "Waiting for frontend to be ready..."
    for i in {1..30}; do
        if curl -s http://localhost:3000/ >/dev/null 2>&1; then
            print_success "Frontend is ready!"
            break
        fi
        if [ $i -eq 30 ]; then
            print_warning "Frontend may not be fully ready yet"
        fi
        sleep 2
    done
}

# Function to show running services
show_services() {
    print_header "🚀 Sample Multi Agent RAG LLM Chatbot is Running!"
    echo ""
    echo -e "${CYAN}📡 Backend API:${NC}     http://localhost:8000"
    echo -e "${CYAN}🌐 Frontend App:${NC}    http://localhost:3000"
    echo -e "${CYAN}📖 API Docs:${NC}        http://localhost:8000/docs (disabled)"
    echo ""
    echo -e "${YELLOW}📋 Logs:${NC}"
    echo -e "   Backend: backend.log"
    echo -e "   Frontend: frontend.log"
    echo ""
    echo -e "${YELLOW}🛑 To stop:${NC} Press Ctrl+C or run: ./stop.sh"
    echo ""
}

# Function to monitor processes
monitor_processes() {
    while true; do
        if ! kill -0 $BACKEND_PID 2>/dev/null; then
            print_error "Backend process died unexpectedly"
            exit 1
        fi
        if ! kill -0 $FRONTEND_PID 2>/dev/null; then
            print_error "Frontend process died unexpectedly"
            exit 1
        fi
        sleep 5
    done
}

# Cleanup function for graceful shutdown
cleanup() {
    print_status "Shutting down services..."
    if [ ! -z "$BACKEND_PID" ] && kill -0 $BACKEND_PID 2>/dev/null; then
        kill $BACKEND_PID
        print_status "Backend stopped"
    fi
    if [ ! -z "$FRONTEND_PID" ] && kill -0 $FRONTEND_PID 2>/dev/null; then
        kill $FRONTEND_PID
        print_status "Frontend stopped"
    fi
    print_success "Cleanup complete"
    exit 0
}

# Set trap for graceful shutdown
trap cleanup SIGINT SIGTERM

# Main execution
main() {
    print_header "🤖 Sample Multi Agent RAG LLM Chatbot"
    print_status "Starting full-stack application..."
    
    # Cleanup any existing processes
    cleanup_ports
    
    # Setup services
    setup_backend
    setup_frontend
    
    # Start services
    start_backend
    start_frontend
    
    # Wait for services to be ready
    wait_for_services
    
    # Show service information
    show_services
    
    # Monitor processes
    monitor_processes
}

# Parse command line arguments
case "${1:-}" in
    --help|-h)
        echo "Usage: $0 [OPTIONS]"
        echo ""
        echo "Start the Sample Multi Agent RAG LLM Chatbot"
        echo ""
        echo "OPTIONS:"
        echo "  --help, -h     Show this help message"
        echo "  --setup-only   Only setup dependencies, don't start services"
        echo ""
        echo "Examples:"
        echo "  $0              # Start both backend and frontend"
        echo "  $0 --setup-only # Only install dependencies"
        exit 0
        ;;
    --setup-only)
        print_header "🔧 Setup Mode"
        setup_backend
        setup_frontend
        print_success "Setup complete! Run ./start.sh to start services."
        exit 0
        ;;
    "")
        main
        ;;
    *)
        print_error "Unknown option: $1"
        print_status "Use --help for usage information"
        exit 1
        ;;
esac