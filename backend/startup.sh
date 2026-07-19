#!/bin/bash
echo "Forcing package installation..."
python -m pip install --upgrade pip
pip install --no-cache-dir --only-binary=:all: -r requirements.txt

echo "Starting Uvicorn..."
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000