@echo off
REM Phase 4 Test Script for Windows
REM This script starts both the backend and frontend for testing

echo.
echo 🚀 Starting AgentWire Phase 4 Test
echo ==================================
echo.

REM Check if Python is available
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Python not found. Please install Python
    exit /b 1
)

REM Check if npm is available
where npm >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ❌ npm not found. Please install Node.js
    exit /b 1
)

echo ✓ Prerequisites check passed
echo.

echo 📡 Starting AgentWire backend on port 8000...
start "AgentWire Backend" cmd /k "uvicorn agentwire.bus:app --reload --port 8000"

REM Wait for backend to start
timeout /t 3 /nobreak >nul

echo.
echo 🎨 Starting dashboard on port 5173...
echo.
echo Press Ctrl+C to stop both servers
echo.

cd dashboard
npm run dev

REM Note: You'll need to manually close the backend window
