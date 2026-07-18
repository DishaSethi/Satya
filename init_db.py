import os
import psycopg2
from dotenv import load_dotenv


load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

SCHEMA_SQL="""
CREATE EXTENSION IF NOT EXISTS vector;
CREATE TABLE IF NOT EXISTS sellers (
    seller_id VARCHAR(50) PRIMARY KEY,
    company_name VARCHAR(255) NOT NULL,
    trust_score DECIMAL(5, 2) DEFAULT 100.00,
    total_offenses INT DEFAULT 0,
    compliance_status VARCHAR(20) DEFAULT 'ACTIVE',
    is_premium_brand BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS products (
    product_id VARCHAR(50) PRIMARY KEY,
    seller_id VARCHAR(50) REFERENCES sellers(seller_id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    category VARCHAR(100),
    catalog_image_url TEXT NOT NULL,
    visibility_multiplier DECIMAL(3, 2) DEFAULT 1.0,
    ui_warning_patch TEXT,
    is_paused BOOLEAN DEFAULT FALSE,
    is_visually_protected BOOLEAN DEFAULT FALSE,
    catalog_image_embedding vector(1536),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS satya_audit_logs (
    audit_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id VARCHAR(50) REFERENCES products(product_id) ON DELETE CASCADE,
    trigger_type VARCHAR(50) NOT NULL,
    pulse_sentiment_score DECIMAL(3, 2),
    vision_discrepancy_score DECIMAL(5,2),
    executed_action VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS product_image_vector_idx ON products USING hnsw (catalog_image_embedding vector_cosine_ops);




"""


def initialize_database():
    if not DATABASE_URL:
        print("❌ Error: DATABASE_URL is missing from your .env file!")
        return

    print("🚀 Connecting to Azure PostgreSQL Database...")
    try:
        # Establish connection to the remote server
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = True
        cursor = conn.cursor()

        print("🛠️ Executing database schemas and registering pgvector HNSW index...")
        cursor.execute(SCHEMA_SQL)

        print("✅ Success! Database schemas fully deployed and ready for Project Satya.")

        # Close connection channels safely
        cursor.close()
        conn.close()

    except Exception as e:
        print(f"❌ Database Initialization Failed: {e}")

if __name__ == "__main__":
    initialize_database()