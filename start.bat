@echo off
title Save Our Memory - Private Digital Sanctuary
color 0F

echo ==============================================================
echo           Save Our Memory - Private Digital Sanctuary
echo ==============================================================
echo.

:: Check for python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not found in PATH!
    echo Please install Python 3.10+ from python.org and add it to PATH.
    pause
    exit /b 1
)

:: Install / Verify dependencies
echo [1/3] Checking dependencies...
python -m pip install -q -r requirements.txt

:: Ensure storage and seed database if missing
echo [2/3] Checking database and media assets...
if not exist "storage\database.sqlite" (
    echo Database not found. Seeding initial demo data...
    python backend\seed.py
)

:: Launch browser in background after 2 seconds
echo [3/3] Starting server on http://127.0.0.1:5000 ...
start "" cmd /c "timeout /t 2 /nobreak >nul & start http://127.0.0.1:5000"

:: Start Flask app
python backend\app.py

pause
