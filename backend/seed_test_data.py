import os
import io
import numpy as np
from PIL import Image
from dotenv import load_dotenv
import psycopg2
from sentence_transformers import SentenceTransformer

# Load credentials
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

print("🧠 Loading CLIP Vision Model...")
model = SentenceTransformer('clip-ViT-B-32')

def seed_database(image_path: str):
    print("🚀 Connecting to Azure...")
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()

    try:
        # 1. Create the Sellers
        print("👥 Creating Test Sellers...")
        sellers_data = [
            ("sell_brand_001", "Satya Premium Boutique", 100.0, True),
            ("sell_rogue_999", "Shady Knockoffs LLC", 40.0, False),
            ("sell_auth_002", "Verified Retailer Inc", 98.0, False)
        ]
        for s_id, name, score, is_premium in sellers_data:
            cursor.execute("""
                INSERT INTO sellers (seller_id, company_name, trust_score, is_premium_brand)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (seller_id) DO NOTHING;
            """, (s_id, name, score, is_premium))

        # 2. Grant Authorization (Premium Boutique authorizes Verified Retailer)
        print("🤝 Granting Brand Authorization...")
        cursor.execute("""
            INSERT INTO seller_brand_authorizations (reseller_seller_id, brand_seller_id)
            VALUES ('sell_auth_002', 'sell_brand_001')
            ON CONFLICT DO NOTHING;
        """)

        # 3. Vectorize and Insert the Protected Asset
        print(f"🖼️ Vectorizing test image: {image_path}")
        pil_image = Image.open(image_path)
        raw_vector = model.encode(pil_image)
        padded_vector = np.pad(raw_vector, (0, 1024), 'constant').tolist()

        print("🔒 Saving Protected Asset to Database...")
        cursor.execute("""
            INSERT INTO products (product_id, seller_id, title, category, catalog_image_url, is_visually_protected, catalog_image_embedding)
            VALUES ('prod_original_1', 'sell_brand_001', 'Premium Signature Jacket', 'Apparel', 'https://satya/jacket.jpg', True, %s)
            ON CONFLICT (product_id) DO NOTHING;
        """, (padded_vector,))

        conn.commit()
        print("✅ Success! The Satya Ecosystem is seeded and ready for testing.")

    except Exception as e:
        conn.rollback()
        print(f"❌ Error: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    # Put the exact name of an image file you have on your MacBook here
    target_image = input("Drag and drop a test image file into this terminal and press Enter: ").strip().strip("'")
    seed_database(target_image)