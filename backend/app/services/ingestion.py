import uuid
import io
import json
import numpy as np
from PIL import Image
from fastapi import UploadFile, HTTPException
from sentence_transformers import SentenceTransformer

vision_model = None

def get_vision_model():
    """Lazy-loads the CLIP model to prevent memory bottlenecks on startup."""
    global vision_model
    if vision_model is None:
        print("🧠 Loading CLIP Vision Model...")
        vision_model = SentenceTransformer('clip-ViT-B-32')
    return vision_model


async def evaluate_ingestion_rules(conn, seller_id: str, vector_embedding: list) -> dict:
    """
    Core Business Logic Engine via asyncpg.
    Executes the pgvector HNSW search and evaluates the 4 Ingestion Cases.
    """
    # Find the single closest visual match with a distance < 0.04 (Similarity > 0.96)
    # Note: asyncpg requires a string representation of lists for vector columns: str(vector_embedding)
    match_query = """
        SELECT p.product_id, p.is_visually_protected, s.seller_id, s.company_name
        FROM products p
        JOIN sellers s ON p.seller_id = s.seller_id
        WHERE (p.catalog_image_embedding <=> $1::vector) < 0.04
        ORDER BY (p.catalog_image_embedding <=> $1::vector) ASC
        LIMIT 1;
    """
    closest_match = await conn.fetchrow(match_query, str(vector_embedding))

    # CASE 0: Unique Product (No close visual match found)
    if not closest_match:
        return {"action": "INSERT", "status": "NEW_PRODUCT", "cluster_id": None}

    # asyncpg fields can be accessed as dict keys or tuple indices
    matched_prod_id = closest_match['product_id']
    is_protected = closest_match['is_visually_protected']
    brand_seller_id = closest_match['seller_id']
    brand_name = closest_match['company_name']

    # If the seller is uploading their own image again, treat as unique/update
    if seller_id == brand_seller_id:
        return {"action": "INSERT", "status": "NEW_PRODUCT", "cluster_id": None}

    # CASE 1: Legitimate Generic Reseller
    if not is_protected:
        return {"action": "INSERT", "status": "CLUSTERED_GENERIC", "cluster_id": matched_prod_id}

    # CASE 2 & 3: Product is Protected - Check Authorization Ledger
    auth_query = """
        SELECT 1 FROM seller_brand_authorizations
        WHERE reseller_seller_id = $1 AND brand_seller_id = $2;
    """
    is_authorized = await conn.fetchval(auth_query, seller_id, brand_seller_id)

    # CASE 2: Branded Authorization Pass
    if is_authorized:
        return {"action": "INSERT", "status": "CLUSTERED_BRAND", "cluster_id": matched_prod_id}

    # CASE 3: Intellectual Property Theft (Protected & Not Authorized)
    raise HTTPException(
        status_code=403,
        detail={
            "status": "IP_THEFT_BLOCKED",
            "message": f"Upload blocked. High visual similarity to protected asset owned by {brand_name}.",
            "matched_product": matched_prod_id
        }
    )


async def process_catalog_upload(seller_id: str, title: str, category: str,public_image_url: str, image: UploadFile, pool) -> dict:
    """Gateway function handling file I/O, ML vectorization, and asyncpg DB pool orchestration."""
    file_bytes = await image.read()

    try:
        pil_image = Image.open(io.BytesIO(file_bytes))
        model = get_vision_model()

        # Keep execution inside a threadpool if it blocks the loop slightly,
        # but standard encoding works fine here for a prototype.
        raw_vector = model.encode(pil_image)
        # Pad to 1536D for Azure pgvector schema
        padded_vector = np.pad(raw_vector, (0, 1024), 'constant').tolist()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Vision Model failed: {str(e)}")

    # Acquire a dedicated connection from the Azure Database for PostgreSQL pool
    async with pool.acquire() as conn:
        # Wrap everything in an explicit database transaction block
        async with conn.transaction():
            try:
                # Evaluate against the state machine logic
                decision = await evaluate_ingestion_rules(conn, seller_id, padded_vector)

                # Generate IDs and file pathways
                product_id = f"prod_{uuid.uuid4().hex[:8]}"
                image_url = public_image_url

                insert_query = """
                    INSERT INTO products (product_id, seller_id, title, category, catalog_image_url, catalog_image_embedding, cluster_id)
                    VALUES ($1, $2, $3, $4, $5, $6::vector, $7)
                    RETURNING product_id;
                """

                # Execute the atomic database write
                await conn.execute(
                    insert_query,
                    product_id,
                    seller_id,
                    title,
                    category,
                    image_url,
                    str(padded_vector),
                    decision["cluster_id"]
                )

                return {
                    "transaction": "SUCCESS",
                    "mvp_status": decision["status"],
                    "product_id": product_id,
                    "cluster_assigned": decision["cluster_id"]
                }

            except HTTPException:
                # Allow Case 3 HTTP 403 blocks to pass through cleanly
                raise
            except Exception as e:
                # The async with conn.transaction() context automatically triggers a rollback here
                raise HTTPException(status_code=500, detail=f"Transaction failed: {str(e)}")