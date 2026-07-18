import json
from fastapi import APIRouter, Request, HTTPException, Form, File, UploadFile
from app.services.blob_service import upload_image_to_azure
from app.services.ingestion import process_catalog_upload

router = APIRouter(prefix="/api/seller", tags=["Seller Gateway"])

@router.post("/upload-catalog")
async def upload_catalog(
    request: Request,
    seller_id: str = Form(...),
    title: str = Form(...),
    category: str = Form(...),
    # public_image_url: str = Form(default=None, description="Optional public URL fallback"),
    image: UploadFile = File(...)
):
    """
    Gateway endpoint for seller catalog uploads.
    Streams file bytes to Azure Blob Storage, then routes the cloud URL to the ingestion service.
    """
    pool = request.app.state.db_pool

    try:
        # 1. Read the raw incoming binary stream from the multi-part form data
        file_bytes = await image.read()
        if not file_bytes:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")

        print(f"📦 [STORAGE] Streaming file asset '{image.filename}' directly to Azure Cloud...")

        # 2. Upload the raw file bytes securely into your Azure Blob container
        azure_blob_url = await upload_image_to_azure(file_bytes, image.filename)
        print(f"🔗 [STORAGE] Asset uploaded successfully. Public Cloud URL: {azure_blob_url}")
        await image.seek(0)

        # 3. Route the execution to the ingestion engine using the fresh Azure URL
        # Note: We pass azure_blob_url as the primary image URL parameter so Gemini and your DB use the cloud resource!
        result = await process_catalog_upload(
            seller_id=seller_id,
            title=title,
            category=category,
            public_image_url=azure_blob_url, # Now pointing securely to your Azure container
            image=image,
            pool=pool
        )
        return result

    except HTTPException as http_err:
        raise http_err
    except Exception as e:
        print(f"⚠️ [API ERROR] Catalog upload funnel failed: {e}")
        raise HTTPException(status_code=500, detail=f"Cloud asset ingestion failed: {str(e)}")



@router.get("/{seller_id}")
async def get_seller_stats(request: Request, seller_id: str):
    """
    Fetches the live Trust Score and Offense count for a specific seller.
    """
    pool = request.app.state.db_pool

    try:
        async with pool.acquire() as conn:
            seller_record = await conn.fetchrow(
                """
                SELECT trust_score, total_offenses, is_premium_brand
                FROM sellers
                WHERE seller_id = $1
                """,
                seller_id
            )

            if not seller_record:
                raise HTTPException(status_code=404, detail="Seller not found")

            return {
                "id": seller_id,
                "name": "Satya Premium Boutique", # Hardcoded name for MVP demo
                "trustScore": float(seller_record['trust_score']),
                "totalOffenses": seller_record['total_offenses'],
                "isPremium": seller_record['is_premium_brand']
            }

    except Exception as e:
        print(f"Database error in seller fetch: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch seller stats")




@router.get("/{seller_id}/catalog")
async def get_seller_catalog(request: Request, seller_id: str):
    """
    Fetches the live product catalog for a specific seller.
    """
    pool = request.app.state.db_pool

    try:
       # INSIDE your catalog endpoint:
        async with pool.acquire() as conn:
            db_products = await conn.fetch("""
                SELECT product_id, title, cluster_id, ui_warning_patch, is_visually_protected
                FROM products
                WHERE seller_id = $1
            """, seller_id)

        catalog = []
        for p in db_products:
            # Update the status logic to be smarter
            if p['ui_warning_patch']:
                status = "FLAGGED_WARNING"
                detail = "Visual Discrepancy Reported"
            elif p['is_visually_protected']:
                status = "PROTECTED_ASSET"
                detail = "IP Registered & Protected"
            elif p['cluster_id']:
                status = "CLUSTERED_GENERIC"
                detail = "Price Comparison Enabled"
            else:
                status = "ACTIVE"
                detail = "Baseline Vector Generated"

            catalog.append({
                "id": p['product_id'],
                "title": p['title'],
                "status": status,
                "detail": detail,
                "isProtected": p['is_visually_protected']
            })

        return catalog

    except Exception as e:
        print(f"Database error in catalog fetch: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch catalog")

