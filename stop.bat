@echo off
REM =============================================================================
REM Sample Multi Agent RAG LLM Chatbot - Windows Stop Script
REM =============================================================================
REM This script stops both backend and frontend services
REM =============================================================================

echo ================================
echo 🛑 Stopping Sample Multi Agent RAG LLM Chatbot
echo ================================

echo [INFO] Stopping backend processes...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000') do (
    taskkill /F /PID %%a >nul 2>&1
)

echo [INFO] Stopping frontend processes...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :3000') do (
    taskkill /F /PID %%a >nul 2>&1
)

REM Kill any uvicorn processes
taskkill /F /IM uvicorn.exe >nul 2>&1

REM Kill any node processes running our app
for /f "tokens=2" %%a in ('tasklist /FI "IMAGENAME eq node.exe" /FO CSV ^| findstr "node.exe"') do (
    taskkill /F /PID %%a >nul 2>&1
)

REM Clean up log files
if exist "backend.log" (
    echo [INFO] Cleaning up backend.log
    del /f "backend.log" >nul 2>&1
)

if exist "frontend.log" (
    echo [INFO] Cleaning up frontend.log
    del /f "frontend.log" >nul 2>&1
)

echo [SUCCESS] All services stopped successfully
echo.
echo [INFO] You can start the application again with: start.bat
pause