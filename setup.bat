@echo off
echo ====================================
echo SP Cloud Bot - Setup Script
echo ====================================
echo.

echo Step 1: Creating virtual environment...
python -m venv venv
if %errorlevel% neq 0 (
    echo ERROR: Failed to create virtual environment
    echo Make sure Python 3.11+ is installed
    pause
    exit /b 1
)
echo Virtual environment created!
echo.

echo Step 2: Activating virtual environment...
call venv\Scripts\activate.bat
echo.

echo Step 3: Installing dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)
echo Dependencies installed!
echo.

echo Step 4: Checking for .env file...
if not exist .env (
    echo WARNING: .env file not found!
    echo Please create .env file from .env.example and add your credentials:
    echo   1. Copy .env.example to .env
    echo   2. Add your BOT_TOKEN from @BotFather
    echo   3. Add your DATABASE_URL
    echo.
    echo Creating .env from example...
    copy .env.example .env
    echo.
    echo Please edit .env file with your actual credentials before running the bot.
    echo.
) else (
    echo .env file found!
)

echo.
echo ====================================
echo Setup Complete!
echo ====================================
echo.
echo Next steps:
echo   1. Edit .env file with your credentials
echo   2. Ensure PostgreSQL is running
echo   3. Create database: CREATE DATABASE sp_cloud;
echo   4. Run: python bot.py
echo.
pause
