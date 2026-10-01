#!/usr/bin/env bash
set -e

echo "=============================================================="
echo "          Save Our Memory - Private Digital Sanctuary"
echo "=============================================================="
echo ""

# Check python
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] python3 could not be found."
    exit 1
fi

echo "[1/3] Checking dependencies..."
python3 -m pip install -q -r requirements.txt

echo "[2/3] Checking database..."
if [ ! -f "storage/database.sqlite" ]; then
    echo "Seeding database with demo data..."
    python3 backend/seed.py
fi

echo "[3/3] Starting server on http://127.0.0.1:5000 ..."
python3 backend/app.py
