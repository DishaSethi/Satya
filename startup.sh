#!/bin/bash
echo "Forcing package installation..."
python -m pip install --upgrade pip
pip install -r backend/requirements.txt

echo "Starting Uvicorn..."
python -m uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8000