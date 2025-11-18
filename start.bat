@echo off
echo Starting AI-Powered Web Scraping Platform...
echo.

REM Check if .env exists
if not exist .env (
    echo WARNING: .env file not found!
    echo Please create a .env file with your GEMINI_API_KEY
    echo See SETUP.md for instructions
    echo.
    pause
)

REM Check if virtual environment exists, if not suggest creating one
python app.py

