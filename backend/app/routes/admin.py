

from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
import asyncpg

router = APIRouter(prefix="/api/admin", tags=["Governance Admin"])
class ResolveAuditRequest(BaseModel):
    audit_id: str
    resolution: str

@router.get("/audit")
async def get_audit_queue(request: Request):
    """
    Fetches flagged events directly from the lean satya_audit_logs table.
    """
    pool = request.app.state.db_pool

    try:
        async with pool.acquire() as conn:
            # FIX 1: Removed the "WHERE" clause so we can see ADMIN_PENDING and PASS too!
            # Added a.product_id so React knows which product to patch.
            db_logs = await conn.fetch("""
                SELECT
                    a.audit_id,
                    a.product_id,
                    a.pulse_sentiment_score,
                    a.vision_discrepancy_score,
                    a.executed_action,
                    a.event_details,
                    p.title AS product_name,
                    p.seller_id,
                    s.trust_score
                FROM satya_audit_logs a
                LEFT JOIN products p ON a.product_id = p.product_id
                LEFT JOIN sellers s ON p.seller_id = s.seller_id
                ORDER BY a.created_at DESC
            """)

        audit_queue = []
        for row in db_logs:
            log = dict(row)

            # Safely get values using .get() to prevent KeyErrors
            sentiment = float(log.get('pulse_sentiment_score') or 0.0)
            vision = float(log.get('vision_discrepancy_score') or 0.0)
            is_scam = (sentiment < 0)

            # Safely fetch the agent reasoning, with a fallback if it is NULL
            agent_reasoning = log.get('event_details')
            if not agent_reasoning:
                agent_reasoning = "⚠️ Swarm telemetry missing or null for this record."

            # FIX 2: Passed the exact fields React expects, especially 'executed_action'
            audit_queue.append({
                "audit_id": str(log.get('audit_id')),
                "product_id": log.get('product_id') or "Unknown ID",
                "product_name": log.get('product_name') or "Unknown Product",
                "seller_id": log.get('seller_id'),
                "trust_score": float(log.get('trust_score') or 0.0),
                "pulse_sentiment_score": sentiment,
                "vision_discrepancy_score": vision,
                "scamIntent": is_scam,
                "executed_action": log.get('executed_action'), # CRITICAL: Tells React what buttons to show!
                "event_details": agent_reasoning
            })

        return audit_queue

    except Exception as e:
        print(f"Database error in audit fetch: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch audit logs")





@router.post("/resolve")
async def resolve_audit(request: Request, payload: ResolveAuditRequest):
    """
    Executes the human-in-the-loop decision and commits it to PostgreSQL.
    """
    pool = request.app.state.db_pool
    audit_id = payload.audit_id
    resolution = payload.resolution

    async with pool.acquire() as conn:
        # 1. Fetch the product_id attached to this audit log
        audit_record = await conn.fetchrow(
            "SELECT product_id FROM satya_audit_logs WHERE audit_id = $1::uuid",
            audit_id
        )

        if not audit_record:
            raise HTTPException(status_code=404, detail="Audit log not found")

        product_id = audit_record['product_id']

        # 2. Execute specific business logic based on Admin's choice
        if resolution == 'APPROVE_PATCH':
            print(f"🛑 [ADMIN] Approving UI Patch for Product: {product_id}")

            # Find the seller who owns this product
            prod_record = await conn.fetchrow(
                "SELECT seller_id FROM products WHERE product_id = $1",
                product_id
            )

            if prod_record:
                seller_id = prod_record['seller_id']
                # Apply the Trust Score penalty!
                await conn.execute(
                    "UPDATE sellers SET trust_score = trust_score - 15, total_offenses = total_offenses + 1 WHERE seller_id = $1",
                    seller_id
                )

            # Apply the Warning Patch to the Marketplace!
            await conn.execute(
                "UPDATE products SET ui_warning_patch = '⚠️ Proceed with Caution: Visual Discrepancy Reported' WHERE product_id = $1",
                product_id
            )

        elif resolution == 'BAN_USER':
            print(f"🔨 [ADMIN] Malicious User Banned for Review Bombing Product: {product_id}")
            # (If you had a users table, you would run the ban query here)

        else:
            print(f"✅ [ADMIN] Action {resolution} acknowledged. Clearing log.")

        # 3. Clean up the queue: Delete the log now that it has been resolved by a human
        await conn.execute(
            "DELETE FROM satya_audit_logs WHERE audit_id = $1::uuid",
            audit_id
        )

    return {"status": "SUCCESS", "message": f"Action {resolution} committed to database."}



@router.put("/products/{product_id}/protect")
async def protect_product(request: Request, product_id: str):
    """Allows a seller to register their product as a protected visual asset."""
    pool = request.app.state.db_pool
    try:
        async with pool.acquire() as conn:
            await conn.execute(
                "UPDATE products SET is_visually_protected = true WHERE product_id = $1",
                product_id
            )
        return {"status": "success", "message": "Asset visually protected"}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to protect asset")
