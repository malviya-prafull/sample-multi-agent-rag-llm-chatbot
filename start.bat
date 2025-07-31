@echo off
REM =============================================================================
REM Sample Multi Agent RAG LLM Chatbot - Windows Start Script
REM =============================================================================
REM This script starts both backend and frontend services simultaneously
REM =============================================================================

setlocal enabledelayedexpansion

REM Colors (limited in Windows)
set "INFO=[INFO]"
set "SUCCESS=[SUCCESS]"
set "WARNING=[WARNING]"
set "ERROR=[ERROR]"

echo ================================
echo Sample Multi Agent RAG LLM Chatbot
echo ================================
echo Starting full-stack application...

REM Function to check if a command exists
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo %ERROR% Python is not installed or not in PATH
    echo Please install Python 3.13+ and try again
    pause
    exit /b 1
)

where node >nul 2>&1
if %errorlevel% neq 0 (
    echo %ERROR% Node.js is not installed or not in PATH
    echo Please install Node.js 18+ and try again
    pause
    exit /b 1
)

echo %INFO% Python version:
python --version

echo %INFO% Node.js version:
node --version

REM Setup Backend
echo.
echo ================================
echo Setting up Backend
echo ================================

cd backend

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo %INFO% Creating virtual environment...
    python -m venv venv
    echo %SUCCESS% Virtual environment created
) else (
    echo %INFO% Virtual environment already exists
)

REM Activate virtual environment
echo %INFO% Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo %INFO% Installing Python dependencies...
pip install -r requirements.txt >nul 2>&1
if %errorlevel% neq 0 (
    echo %ERROR% Failed to install Python dependencies
    pause
    exit /b 1
)
echo %SUCCESS% Dependencies installed

REM Check if .env file exists
if not exist ".env" (
    echo %WARNING% .env file not found. Creating template...
    echo NVIDIA_API_KEY=your_nvidia_api_key_here > .env
    echo %WARNING% Please add your NVIDIA API key to backend\.env file
)

REM Setup database if needed
if not exist "ecommerce.db" (
    echo %INFO% Setting up database and vector store...
    python data_script.py
    if %errorlevel% neq 0 (
        echo %ERROR% Failed to setup database
        pause
        exit /b 1
    )
    echo %SUCCESS% Database and vector store setup complete
) else (
    echo %INFO% Database already exists
)

cd ..

REM Setup Frontend
echo.
echo ================================
echo Setting up Frontend
echo ================================

cd frontend

REM Install dependencies if node_modules doesn't exist
if not exist "node_modules" (
    echo %INFO% Installing Node.js dependencies...
    npm install >nul 2>&1
    if %errorlevel% neq 0 (
        echo %ERROR% Failed to install Node.js dependencies
        pause
        exit /b 1
    )
    echo %SUCCESS% Dependencies installed
) else (
    echo %INFO% Node.js dependencies already installed
)

cd ..

REM Start services
echo.
echo ================================
echo Starting Services
echo ================================

REM Start backend in background
echo %INFO% Starting backend server...
cd backend
call venv\Scripts\activate.bat
start /b cmd /c "uvicorn main:app --host 0.0.0.0 --port 8000 --reload > ..\backend.log 2>&1"
cd ..

REM Wait a moment
timeout /t 3 /nobreak >nul

REM Start frontend in background
echo %INFO% Starting frontend server...
cd frontend
set PORT=3000
start /b cmd /c "npm start > ..\frontend.log 2>&1"
cd ..

REM Wait for services to start
echo %INFO% Waiting for services to start...
timeout /t 10 /nobreak >nul

echo.
echo ================================
echo 🚀 Sample Multi Agent RAG LLM Chatbot is Running!
echo ================================
echo.
echo 📡 Backend API:     http://localhost:8000
echo 🌐 Frontend App:    http://localhost:3000
echo.
echo 📋 Logs:
echo    Backend: backend.log
echo    Frontend: frontend.log
echo.
echo 🛑 To stop: Close this window or run stop.bat
echo.
echo Opening frontend in your default browser...
timeout /t 3 /nobreak >nul

REM Open frontend in browser
start http://localhost:3000

echo.
echo Press any key to monitor logs or Ctrl+C to exit...
pause >nul

REM Show logs (optional)
:monitor
echo Current backend log:
type backend.log | findstr /C:"ERROR" /C:"WARNING" /C:"INFO" 2>nul
echo.
echo Current frontend log:
type frontend.log | findstr /C:"ERROR" /C:"WARNING" /C:"Local:" 2>nul
echo.
timeout /t 10 /nobreak >nul
goto monitor