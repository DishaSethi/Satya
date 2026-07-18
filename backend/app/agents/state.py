from typing import TypedDict, Optional, List

class ProductEvaluationState(TypedDict):
    """
    The SwarmState context for the Post-Purchase Review evaluation.
    """
    # 1. Input Payload (From Queue)
    review_id: str
    product_id: str
    seller_id: str
    review_text: str
    unboxing_image_url: str
    catalog_image_vector: Optional[List[float]]
    product_name: str
    catalog_image_url:str

    # 2. Historical Data (For Scenario C: Review Bombing)
    seller_trust_score: int
    seller_total_offenses: int
    seller_total_transactions: int

    # 3. Vision Node Outputs (768-D Spatial Variance)
    visual_discrepancy_score: Optional[float]
    vision_notes: Optional[str]

    # 4. Pulse Node Outputs (Linguistic Deception)
    text_sentiment: Optional[str]
    scam_intent_detected: Optional[bool]
    pulse_notes: Optional[str]

    # 5. Executive Node Output
    final_decision: Optional[str]  # "PASS", "TRIGGER_UI_PATCH", "FLAG_MANUAL"

    # 6. Telemetry for the Dashboard
    agent_telemetry_logs: List[str]