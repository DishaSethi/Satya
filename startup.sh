#!/bin/bash
echo "Forcing package installation..."
# The --no-cache-dir flag is vital to prevent the hang
# We also use --only-binary=:all: to avoid building heavy packages like torch from source
python -m pip install --upgrade pip
pip install --no-cache-dir --only-binary=:all: -r backend/requirements.txt

echo "Starting Uvicorn..."
python -m uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8000