import os
import json
import uuid
import asyncio
import asyncpg
from dotenv import load_dotenv
load_dotenv()
from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, Form, Request, HTTPException,APIRouter
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.routes import seller, customer, admin
from app.services.queue_service import consume_from_queue


AZURE_PG_URL = os.getenv("DATABASE_URL")
if not AZURE_PG_URL:
    raise ValueError("🚨 FATAL ERROR: DATABASE_URL is missing. Please check your .env file.")

# Import your services
from app.services.ingestion import process_catalog_upload
from app.services.queue_service import publish_to_queue, consume_from_queue


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager: Runs exactly once when the server boots."""
    print("🔌 Booting Azure PostgreSQL Connection Pool...")
    # Initialize the raw SQL connection pool for maximum performance
    app.state.db_pool = await asyncpg.create_pool(dsn=AZURE_PG_URL)

    print("🚀 Waking up LangGraph Swarm Background Worker...")
    # FIX #1: Pass the db_pool to the worker so it can save AI decisions
    worker_task = asyncio.create_task(consume_from_queue(app.state.db_pool))

    yield  # The FastAPI server runs while yielding here

    print("🛑 Shutting down gracefully...")
    worker_task.cancel()
    await app.state.db_pool.close()

app = FastAPI(
    title="Project Satya API",
    description="E-commerce AI Governance & Guardrail System",
    version="2.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(seller.router)
app.include_router(customer.router)
app.include_router(admin.router)
@app.get("/")
def read_root():
    return {"status": "Satya Gateway Engine is Online with Clean Architecture"}





# @app.post("/upload-catalog")
# async def upload_catalog(
#     request: Request, # FIX #2: Added request to access the db_pool
#     seller_id: str = Form(...),
#     title: str = Form(...),
#     category: str = Form(...),
#     public_image_url: str = Form(..., description="Paste a public Unsplash URL here for Gemini to use"),
#     image: UploadFile = File(...)
# ):
#     """Gateway endpoint for seller catalog uploads. Routes to the ingestion service."""
#     pool = request.app.state.db_pool
#     # Passed the pool down into the ingestion service
#     result = await process_catalog_upload(seller_id, title, category, public_image_url, image, pool)
#     return result


# @app.post("/submit-review")
# async def submit_buyer_review(
#     request: Request,
#     product_id: str = Form(...),
#     seller_id: str = Form(...),
#     review_text: str = Form(...),
#     unboxing_image_url: str = Form(...)
# ):
#     """Accepts buyer unboxing review, fetches DB context, and triggers the AI Swarm."""
#     pool = request.app.state.db_pool

#     async with pool.acquire() as conn:
#         # FIX #3: Adjusted column names to match your ingestion.py schema
#         product_record = await conn.fetchrow(
#             "SELECT catalog_image_embedding FROM products WHERE product_id = $1",
#             product_id
#         )
#         if not product_record:
#             raise HTTPException(status_code=404, detail="Product not found in catalog.")

#         catalog_vector = json.loads(product_record['catalog_image_embedding'])

#         seller_record = await conn.fetchrow(
#             """
#             SELECT trust_score, total_offenses, total_transactions
#             FROM sellers
#             WHERE seller_id = $1
#             """,
#             seller_id
#         )
#         if not seller_record:
#             raise HTTPException(status_code=404, detail="Seller not found in database.")

#     review_id = f"rev_{uuid.uuid4().hex[:8]}"

#     # Package the fully hydrated state
#     payload = {
#         "review_id": review_id,
#         "product_id": product_id,
#         "seller_id": seller_id,
#         "review_text": review_text,
#         "unboxing_image_url": unboxing_image_url,
#         "catalog_image_vector": catalog_vector,
#         "seller_trust_score": seller_record['trust_score'],
#         "seller_total_offenses": seller_record['total_offenses'],
#         "seller_total_transactions": seller_record['total_transactions']
#     }

#     # Push to async queue
#     await publish_to_queue(payload)

#     return {
#         "transaction": "SUCCESS",
#         "message": "Review queued for Agentic Swarm Analysis.",
#         "review_id": review_id
#     }

# ... (keep your imports and lifespan as they are) ...

# @app.post("/submit-review")
# async def submit_buyer_review(
#     request: Request,
#     product_id: str = Form(...),
#     seller_id: str = Form(...),
#     review_text: str = Form(...),
#     unboxing_image_url: str = Form(...)
# ):
#     """Accepts buyer unboxing review, fetches DB context, and triggers the AI Swarm."""
#     pool = request.app.state.db_pool

#     async with pool.acquire() as conn:
#         product_record = await conn.fetchrow(
#             "SELECT title, catalog_image_url, catalog_image_embedding FROM products WHERE product_id = $1",
#             product_id
#         )
#         if not product_record:
#             raise HTTPException(status_code=404, detail="Product not found in catalog.")

#         catalog_vector = json.loads(product_record['catalog_image_embedding'])

#         # SCHEMA FIX: Removed total_transactions, added is_premium_brand
#         seller_record = await conn.fetchrow(
#             """
#             SELECT trust_score, total_offenses, is_premium_brand
#             FROM sellers
#             WHERE seller_id = $1
#             """,
#             seller_id
#         )
#         if not seller_record:
#             raise HTTPException(status_code=404, detail="Seller not found in database.")

#     review_id = f"rev_{uuid.uuid4().hex[:8]}"

#     # Package the fully hydrated state
#     payload = {
#         "review_id": review_id,
#         "product_id": product_id,
#         "seller_id": seller_id,
#         "review_text": review_text,
#         "unboxing_image_url": unboxing_image_url,
#         "product_name": product_record['title'],          # <--- Added dynamically
#         "catalog_image_url": product_record['catalog_image_url'],
#         "catalog_image_vector": catalog_vector,
#         "seller_trust_score": float(seller_record['trust_score']), # Cast numeric to float
#         "seller_total_offenses": seller_record['total_offenses'],
#         "seller_is_premium": seller_record['is_premium_brand']
#     }

#     await publish_to_queue(payload)

#     return {
#         "transaction": "SUCCESS",
#         "message": "Review queued for Agentic Swarm Analysis.",
#         "review_id": review_id
#     }






# @app.post("/submit-review")
# async def submit_buyer_review(
#     request: Request,
#     product_id: str = Form(...),
#     seller_id: str = Form(...),
#     review_text: str = Form(...),
#     unboxing_image: UploadFile = File(...) # FIX: Changed from string URL to real File upload!
# ):
#     """Accepts buyer unboxing review file, uploads to Azure, fetches DB context, and triggers the AI Swarm."""
#     pool = request.app.state.db_pool

#     try:
#         # 1. Stream the unboxing image to Azure Blob Storage instantly
#         review_bytes = await unboxing_image.read()
#         if not review_bytes:
#             raise HTTPException(status_code=400, detail="Review image file is empty.")

#         print(f"📦 [STORAGE] Uploading unboxing asset '{unboxing_image.filename}' to Azure...")
#         azure_review_image_url = await upload_image_to_azure(review_bytes, unboxing_image.filename)
#         print(f"🔗 [STORAGE] Unboxing asset live at: {azure_review_image_url}")

#         # 2. Hydrate data context from PostgreSQL
#         async with pool.acquire() as conn:
#             product_record = await conn.fetchrow(
#                 "SELECT title, catalog_image_url, catalog_image_embedding FROM products WHERE product_id = $1",
#                 product_id
#             )
#             if not product_record:
#                 raise HTTPException(status_code=404, detail="Product not found in catalog.")

#             catalog_vector = json.loads(product_record['catalog_image_embedding'])

#             # SCHEMA FIX: Removed total_transactions, added is_premium_brand
#             seller_record = await conn.fetchrow(
#                 """
#                 SELECT trust_score, total_offenses, is_premium_brand
#                 FROM sellers
#                 WHERE seller_id = $1
#                 """,
#                 seller_id
#             )
#             if not seller_record:
#                 raise HTTPException(status_code=404, detail="Seller not found in database.")

#         review_id = f"rev_{uuid.uuid4().hex[:8]}"

#         # 3. Package the fully hydrated state using the new Cloud URL
#         payload = {
#             "review_id": review_id,
#             "product_id": product_id,
#             "seller_id": seller_id,
#             "review_text": review_text,
#             "unboxing_image_url": azure_review_image_url,  # <--- Secure Azure URL passed to Swarm!
#             "product_name": product_record['title'],
#             "catalog_image_url": product_record['catalog_image_url'],
#             "catalog_image_vector": catalog_vector,
#             "seller_trust_score": float(seller_record['trust_score']),
#             "seller_total_offenses": seller_record['total_offenses'],
#             "seller_is_premium": seller_record['is_premium_brand']
#         }

#         # 4. Dispatch transaction to Azure Service Bus
#         await publish_to_queue(payload)

#         return {
#             "transaction": "SUCCESS",
#             "message": "Review pushed into Azure Service Bus queue for asynchronous Swarm processing.",
#             "review_id": review_id
#         }

#     except HTTPException as http_err:
#         raise http_err
#     except Exception as e:
#         print(f"⚠️ [API ERROR] Review ingestion funnel failed: {e}")
#         raise HTTPException(status_code=500, detail=f"Review processing failed: {str(e)}")



# @app.get("/api/products")
# async def get_all_products(request: Request):
#     """
#     Fetches all products via asyncpg (raw SQL) and maps them to the React frontend schema.
#     """
#     pool = request.app.state.db_pool

#     try:
#         async with pool.acquire() as conn:
#             # Query the database using raw SQL to match your asyncpg setup
#             db_products = await conn.fetch("""
#                 SELECT
#                     product_id,
#                     title,
#                     seller_id,
#                     catalog_image_url,
#                     ui_warning_patch,
#                     cluster_id,
#                     original_brand
#                 FROM products
#             """)

#         # Map the asyncpg records to the exact JSON structure React expects
#         frontend_products = []
#         for p in db_products:
#             frontend_products.append({
#                 "id": p['product_id'],
#                 "title": p['title'],
#                 "seller": p['seller_id'],
#                 "price": "₹4,500", # Hardcoded for the MVP demo as price isn't in DB yet
#                 "imageUrl": p['catalog_image_url'],

#                 # These fields power the UI alerts in the Customer View
#                 "uiWarningPatch": p['ui_warning_patch'],
#                 "isClusteredMatch": True if p['cluster_id'] else False,
#                 "originalBrand": p['original_brand']
#             })

#         return frontend_products

#     except asyncpg.exceptions.UndefinedColumnError as e:
#         print(f"Schema mismatch: {e}")
#         raise HTTPException(
#             status_code=500,
#             detail="Missing columns in PostgreSQL. Please run your ALTER TABLE statements for ui_warning_patch, cluster_id, and original_brand."
#         )
#     except Exception as e:
#         print(f"Database error: {e}")
#         raise HTTPException(status_code=500, detail="Failed to fetch products from database")


# # @app.get("/api/seller/{seller_id}")
# # async def get_seller_stats(request: Request, seller_id: str):
# #     """
# #     Fetches the live Trust Score and Offense count for a specific seller.
# #     """
# #     pool = request.app.state.db_pool

# #     try:
# #         async with pool.acquire() as conn:
# #             seller_record = await conn.fetchrow(
# #                 """
# #                 SELECT trust_score, total_offenses, is_premium_brand
# #                 FROM sellers
# #                 WHERE seller_id = $1
# #                 """,
# #                 seller_id
# #             )

# #             if not seller_record:
# #                 raise HTTPException(status_code=404, detail="Seller not found")

# #             return {
# #                 "id": seller_id,
# #                 "name": "Satya Premium Boutique", # Hardcoded name for MVP demo
# #                 "trustScore": float(seller_record['trust_score']),
# #                 "totalOffenses": seller_record['total_offenses'],
# #                 "isPremium": seller_record['is_premium_brand']
# #             }

# #     except Exception as e:
# #         print(f"Database error in seller fetch: {e}")
# #         raise HTTPException(status_code=500, detail="Failed to fetch seller stats")


# @app.get("/api/seller/{seller_id}/catalog")
# async def get_seller_catalog(request: Request, seller_id: str):
#     """
#     Fetches the live product catalog for a specific seller.
#     """
#     pool = request.app.state.db_pool

#     try:
#        # INSIDE your catalog endpoint:
#         async with pool.acquire() as conn:
#             db_products = await conn.fetch("""
#                 SELECT product_id, title, cluster_id, ui_warning_patch, is_visually_protected
#                 FROM products
#                 WHERE seller_id = $1
#             """, seller_id)

#         catalog = []
#         for p in db_products:
#             # Update the status logic to be smarter
#             if p['ui_warning_patch']:
#                 status = "FLAGGED_WARNING"
#                 detail = "Visual Discrepancy Reported"
#             elif p['is_visually_protected']:
#                 status = "PROTECTED_ASSET"
#                 detail = "IP Registered & Protected"
#             elif p['cluster_id']:
#                 status = "CLUSTERED_GENERIC"
#                 detail = "Price Comparison Enabled"
#             else:
#                 status = "ACTIVE"
#                 detail = "Baseline Vector Generated"

#             catalog.append({
#                 "id": p['product_id'],
#                 "title": p['title'],
#                 "status": status,
#                 "detail": detail,
#                 "isProtected": p['is_visually_protected']
#             })

#         return catalog

#     except Exception as e:
#         print(f"Database error in catalog fetch: {e}")
#         raise HTTPException(status_code=500, detail="Failed to fetch catalog")


# # @app.get("/api/admin/audit")
# # async def get_audit_queue(request: Request):
# #     """
# #     Fetches flagged events directly from the lean satya_audit_logs table.
# #     """
# #     pool = request.app.state.db_pool

# #     try:
# #         async with pool.acquire() as conn:
# #             # Join products to get the title, and sellers (via products) to get trust_score
# #             db_logs = await conn.fetch("""
# #                 SELECT
# #                     a.audit_id,
# #                     a.pulse_sentiment_score,
# #                     a.vision_discrepancy_score,
# #                     a.executed_action,
# #                     a.event_details,
# #                     p.title AS product_name,
# #                     p.seller_id,
# #                     s.trust_score
# #                 FROM satya_audit_logs a
# #                 LEFT JOIN products p ON a.product_id = p.product_id
# #                 LEFT JOIN sellers s ON p.seller_id = s.seller_id
# #                 WHERE a.executed_action = 'FLAG_MANUAL'
# #                 ORDER BY a.created_at DESC
# #             """)

# #         audit_queue = []
# #         for row in db_logs:
# #             # FIX 2: Convert the asyncpg.Record to a standard Python dictionary
# #             log = dict(row)

# #             # Safely get values using .get() to prevent KeyErrors
# #             sentiment = float(log.get('pulse_sentiment_score') or 0.0)
# #             vision = float(log.get('vision_discrepancy_score') or 0.0)
# #             is_scam = (sentiment < 0) and (vision == 0.0)

# #             # Safely fetch the agent reasoning, with a fallback if it is NULL
# #             agent_reasoning = log.get('event_details')
# #             if not agent_reasoning:
# #                 agent_reasoning = "⚠️ Swarm telemetry missing or null for this record."

# #             audit_queue.append({
# #                 "id": str(log.get('audit_id')),
# #                 "seller": log.get('seller_id'),
# #                 "sellerId": log.get('seller_id'),
# #                 "product": log.get('product_name') or "Unknown Product",
# #                 "text": agent_reasoning,
# #                 "visionScore": vision,
# #                 "scamIntent": is_scam,
# #                 "trustScore": float(log.get('trust_score') or 0.0),
# #                 "reason": "Swarm Anomaly Detected",
# #             })

# #         return audit_queue

# #     except Exception as e:
# #         print(f"Database error in audit fetch: {e}")
# #         raise HTTPException(status_code=500, detail="Failed to fetch audit logs")

# @app.get("/api/admin/audit")
# async def get_audit_queue(request: Request):
#     """
#     Fetches flagged events directly from the lean satya_audit_logs table.
#     """
#     pool = request.app.state.db_pool

#     try:
#         async with pool.acquire() as conn:
#             # FIX 1: Removed the "WHERE" clause so we can see ADMIN_PENDING and PASS too!
#             # Added a.product_id so React knows which product to patch.
#             db_logs = await conn.fetch("""
#                 SELECT
#                     a.audit_id,
#                     a.product_id,
#                     a.pulse_sentiment_score,
#                     a.vision_discrepancy_score,
#                     a.executed_action,
#                     a.event_details,
#                     p.title AS product_name,
#                     p.seller_id,
#                     s.trust_score
#                 FROM satya_audit_logs a
#                 LEFT JOIN products p ON a.product_id = p.product_id
#                 LEFT JOIN sellers s ON p.seller_id = s.seller_id
#                 ORDER BY a.created_at DESC
#             """)

#         audit_queue = []
#         for row in db_logs:
#             log = dict(row)

#             # Safely get values using .get() to prevent KeyErrors
#             sentiment = float(log.get('pulse_sentiment_score') or 0.0)
#             vision = float(log.get('vision_discrepancy_score') or 0.0)
#             is_scam = (sentiment < 0)

#             # Safely fetch the agent reasoning, with a fallback if it is NULL
#             agent_reasoning = log.get('event_details')
#             if not agent_reasoning:
#                 agent_reasoning = "⚠️ Swarm telemetry missing or null for this record."

#             # FIX 2: Passed the exact fields React expects, especially 'executed_action'
#             audit_queue.append({
#                 "audit_id": str(log.get('audit_id')),
#                 "product_id": log.get('product_id') or "Unknown ID",
#                 "product_name": log.get('product_name') or "Unknown Product",
#                 "seller_id": log.get('seller_id'),
#                 "trust_score": float(log.get('trust_score') or 0.0),
#                 "pulse_sentiment_score": sentiment,
#                 "vision_discrepancy_score": vision,
#                 "scamIntent": is_scam,
#                 "executed_action": log.get('executed_action'), # CRITICAL: Tells React what buttons to show!
#                 "event_details": agent_reasoning
#             })

#         return audit_queue

#     except Exception as e:
#         print(f"Database error in audit fetch: {e}")
#         raise HTTPException(status_code=500, detail="Failed to fetch audit logs")

# @app.put("/api/products/{product_id}/protect")
# async def protect_product(request: Request, product_id: str):
#     """Allows a seller to register their product as a protected visual asset."""
#     pool = request.app.state.db_pool
#     try:
#         async with pool.acquire() as conn:
#             await conn.execute(
#                 "UPDATE products SET is_visually_protected = true WHERE product_id = $1",
#                 product_id
#             )
#         return {"status": "success", "message": "Asset visually protected"}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail="Failed to protect asset")




# class ResolveAuditRequest(BaseModel):
#     audit_id: str
#     resolution: str


# @app.post("/api/admin/resolve")
# async def resolve_audit(request: Request, payload: ResolveAuditRequest):
#     """
#     Executes the human-in-the-loop decision and commits it to PostgreSQL.
#     """
#     pool = request.app.state.db_pool
#     audit_id = payload.audit_id
#     resolution = payload.resolution

#     async with pool.acquire() as conn:
#         # 1. Fetch the product_id attached to this audit log
#         audit_record = await conn.fetchrow(
#             "SELECT product_id FROM satya_audit_logs WHERE audit_id = $1::uuid",
#             audit_id
#         )

#         if not audit_record:
#             raise HTTPException(status_code=404, detail="Audit log not found")

#         product_id = audit_record['product_id']

#         # 2. Execute specific business logic based on Admin's choice
#         if resolution == 'APPROVE_PATCH':
#             print(f"🛑 [ADMIN] Approving UI Patch for Product: {product_id}")

#             # Find the seller who owns this product
#             prod_record = await conn.fetchrow(
#                 "SELECT seller_id FROM products WHERE product_id = $1",
#                 product_id
#             )

#             if prod_record:
#                 seller_id = prod_record['seller_id']
#                 # Apply the Trust Score penalty!
#                 await conn.execute(
#                     "UPDATE sellers SET trust_score = trust_score - 15, total_offenses = total_offenses + 1 WHERE seller_id = $1",
#                     seller_id
#                 )

#             # Apply the Warning Patch to the Marketplace!
#             await conn.execute(
#                 "UPDATE products SET ui_warning_patch = '⚠️ Proceed with Caution: Visual Discrepancy Reported' WHERE product_id = $1",
#                 product_id
#             )

#         elif resolution == 'BAN_USER':
#             print(f"🔨 [ADMIN] Malicious User Banned for Review Bombing Product: {product_id}")
#             # (If you had a users table, you would run the ban query here)

#         else:
#             print(f"✅ [ADMIN] Action {resolution} acknowledged. Clearing log.")

#         # 3. Clean up the queue: Delete the log now that it has been resolved by a human
#         await conn.execute(
#             "DELETE FROM satya_audit_logs WHERE audit_id = $1::uuid",
#             audit_id
#         )

#     return {"status": "SUCCESS", "message": f"Action {resolution} committed to database."}