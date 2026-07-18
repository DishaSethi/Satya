import json
import uuid
from fastapi import APIRouter, Request, HTTPException, Form, File, UploadFile
import asyncpg
from app.services.blob_service import upload_image_to_azure
from app.services.queue_service import publish_to_queue

router = APIRouter(prefix="/api/customer", tags=["Customer Gateway"])

@router.post("/submit-review")
async def submit_buyer_review(
    request: Request,
    product_id: str = Form(...),
    seller_id: str = Form(...),
    review_text: str = Form(...),
    unboxing_image: UploadFile = File(...) # FIX: Changed from string URL to real File upload!
):
    """Accepts buyer unboxing review file, uploads to Azure, fetches DB context, and triggers the AI Swarm."""
    pool = request.app.state.db_pool

    try:
        # 1. Stream the unboxing image to Azure Blob Storage instantly
        review_bytes = await unboxing_image.read()
        if not review_bytes:
            raise HTTPException(status_code=400, detail="Review image file is empty.")

        print(f"📦 [STORAGE] Uploading unboxing asset '{unboxing_image.filename}' to Azure...")
        azure_review_image_url = await upload_image_to_azure(review_bytes, unboxing_image.filename)
        print(f"🔗 [STORAGE] Unboxing asset live at: {azure_review_image_url}")

        # 2. Hydrate data context from PostgreSQL
        async with pool.acquire() as conn:
            product_record = await conn.fetchrow(
                "SELECT title, catalog_image_url, catalog_image_embedding FROM products WHERE product_id = $1",
                product_id
            )
            if not product_record:
                raise HTTPException(status_code=404, detail="Product not found in catalog.")

            catalog_vector = json.loads(product_record['catalog_image_embedding'])

            # SCHEMA FIX: Removed total_transactions, added is_premium_brand
            seller_record = await conn.fetchrow(
                """
                SELECT trust_score, total_offenses, is_premium_brand
                FROM sellers
                WHERE seller_id = $1
                """,
                seller_id
            )
            if not seller_record:
                raise HTTPException(status_code=404, detail="Seller not found in database.")

        review_id = f"rev_{uuid.uuid4().hex[:8]}"

        # 3. Package the fully hydrated state using the new Cloud URL
        payload = {
            "review_id": review_id,
            "product_id": product_id,
            "seller_id": seller_id,
            "review_text": review_text,
            "unboxing_image_url": azure_review_image_url,  # <--- Secure Azure URL passed to Swarm!
            "product_name": product_record['title'],
            "catalog_image_url": product_record['catalog_image_url'],
            "catalog_image_vector": catalog_vector,
            "seller_trust_score": float(seller_record['trust_score']),
            "seller_total_offenses": seller_record['total_offenses'],
            "seller_is_premium": seller_record['is_premium_brand']
        }

        # 4. Dispatch transaction to Azure Service Bus
        await publish_to_queue(payload)

        return {
            "transaction": "SUCCESS",
            "message": "Review pushed into Azure Service Bus queue for asynchronous Swarm processing.",
            "review_id": review_id
        }

    except HTTPException as http_err:
        raise http_err
    except Exception as e:
        print(f"⚠️ [API ERROR] Review ingestion funnel failed: {e}")
        raise HTTPException(status_code=500, detail=f"Review processing failed: {str(e)}")




@router.get("/products")
async def get_all_products(request: Request):
    """
    Fetches all products via asyncpg (raw SQL) and maps them to the React frontend schema.
    """
    pool = request.app.state.db_pool

    try:
        async with pool.acquire() as conn:
            # Query the database using raw SQL to match your asyncpg setup
            db_products = await conn.fetch("""
                SELECT
                    product_id,
                    title,
                    seller_id,
                    catalog_image_url,
                    ui_warning_patch,
                    cluster_id,
                    original_brand
                FROM products
            """)

        # Map the asyncpg records to the exact JSON structure React expects
        frontend_products = []
        for p in db_products:
            frontend_products.append({
                "id": p['product_id'],
                "title": p['title'],
                "seller": p['seller_id'],
                "price": "₹4,500", # Hardcoded for the MVP demo as price isn't in DB yet
                "imageUrl": p['catalog_image_url'],

                # These fields power the UI alerts in the Customer View
                "uiWarningPatch": p['ui_warning_patch'],
                "isClusteredMatch": True if p['cluster_id'] else False,
                "originalBrand": p['original_brand']
            })

        return frontend_products

    except asyncpg.exceptions.UndefinedColumnError as e:
        print(f"Schema mismatch: {e}")
        raise HTTPException(
            status_code=500,
            detail="Missing columns in PostgreSQL. Please run your ALTER TABLE statements for ui_warning_patch, cluster_id, and original_brand."
        )
    except Exception as e:
        print(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch products from database")

