import psycopg2
import os
from dotenv import load_dotenv
from fastapi import HTTPException

# Load environment variables
load_dotenv(dotenv_path="../.env")
DATABASE_URL = os.getenv("DATABASE_URL")

def get_db_connection():
    """Live connection pooler to Azure PostgreSQL."""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {e}")