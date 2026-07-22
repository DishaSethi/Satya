# Use the official Python 3.11 image
FROM python:3.11-slim-bullseye

# Set the working directory
WORKDIR /app

# Install system dependencies needed for C-extensions
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker layer caching
COPY requirements.txt .

# Install dependencies cleanly
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application code
COPY . .

# Expose Uvicorn port
EXPOSE 8000

# Start Uvicorn server
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]