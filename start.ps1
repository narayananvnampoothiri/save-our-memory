# Save Our Memory - PowerShell Startup Script
Write-Host "==============================================================" -ForegroundColor Cyan
Write-Host "          Save Our Memory - Private Digital Sanctuary" -ForegroundColor Yellow
Write-Host "==============================================================" -ForegroundColor Cyan
Write-Host ""

# Verify Python
try {
    $pyVersion = python --version
    Write-Host "[1/3] Found $pyVersion" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Python is not installed or not in PATH." -ForegroundColor Red
    Exit 1
}

# Install / verify requirements
Write-Host "[2/3] Checking dependencies..." -ForegroundColor Cyan
python -m pip install -q -r requirements.txt

# Seed if missing
if (-not (Test-Path "storage\database.sqlite")) {
    Write-Host "Seeding database with demo memories..." -ForegroundColor Yellow
    python backend\seed.py
}

# Open browser and run
Write-Host "[3/3] Starting server on http://127.0.0.1:5000 ..." -ForegroundColor Green
Start-Process "http://127.0.0.1:5000"

python backend\app.py
