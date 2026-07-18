import os
import json
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
from app.agents.state import ProductEvaluationState

llm_exec = ChatGroq(
    model="llama-3.1-8b-instant",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.0
)

def make_final_decision(state: ProductEvaluationState) -> ProductEvaluationState:
    """
    The Executive Node: Hybrid Governance Engine.
    Uses strict Python logic for the penalty decision to prevent hallucinations,
    then uses Llama-3 to generate a contextual explanation for the UI.
    """
    print(f"⚖️ [EXECUTIVE NODE] Synthesizing data for review: {state['review_id']}")

    if 'agent_telemetry_logs' not in state or state['agent_telemetry_logs'] is None:
        state['agent_telemetry_logs'] = []

    variance = state.get('visual_discrepancy_score', 0.0)
    scam_intent = state.get('scam_intent_detected', False)
    trust_score = state.get('seller_trust_score', 100)
    transactions = state.get('seller_total_transactions', 0)

    VARIANCE_THRESHOLD = 0.35

    # ---------------------------------------------------------------------
    # STEP 1: DETERMINISTIC ROUTING (No Hallucinations Allowed)
    # ---------------------------------------------------------------------
    # if variance > VARIANCE_THRESHOLD and trust_score >= 90 and state.get('seller_total_offenses', 0) == 0:
    #     decision = "FLAG_MANUAL"
    #     scenario_context = "Suspicious Buyer Claim against Top Seller"
    # elif variance <= VARIANCE_THRESHOLD and scam_intent and trust_score >= 90:
    #     decision = "FLAG_MANUAL"
    #     scenario_context = "Competitor Review Bombing Suspected"
    # elif variance > VARIANCE_THRESHOLD or (scam_intent and trust_score < 90):
    #     decision = "TRIGGER_UI_PATCH"
    #     scenario_context = "Seller Fraud / Bait & Switch Detected"
    # else:
    #     decision = "PASS"
    #     scenario_context = "Normal Verified Pass"

    # # Save the strict decision to state so the database worker can execute it safely
    # state['final_decision'] = decision

    if variance > VARIANCE_THRESHOLD and trust_score >= 90 and state.get('seller_total_offenses', 0) == 0:
        # Image looks bad, BUT it's a flawless seller.
        # The buyer might be uploading a fake photo to scam the seller.
        decision = "FLAG_MANUAL"
        scenario_context = "Suspicious Buyer Image against Top Seller - Needs Audit"

    elif variance > VARIANCE_THRESHOLD:
        # Standard or low-trust seller with a bad image. Likely a real Bait & Switch.
        # Replaces TRIGGER_UI_PATCH so it goes to the Admin first.
        decision = "ADMIN_PENDING"
        scenario_context = "Seller Fraud / Bait & Switch Detected - Pending Admin UI Patch"

    elif scam_intent:
        # The picture proves the item is PERFECT (variance <= 0.35), but the buyer is screaming "SCAM".
        # This protects ALL sellers (high and low trust) from malicious review bombing.
        decision = "FLAG_MANUAL"
        scenario_context = "Competitor Review Bombing (Visual evidence contradicts buyer text)"

    else:
        # Everything aligns perfectly.
        decision = "PASS"
        scenario_context = "Authentic Transaction Verified - Trust Score Increased"

    state['final_decision'] = decision

    # ---------------------------------------------------------------------
    # STEP 2: GENERATIVE EXPLANATION (Llama-3 drafts the Dashboard Note)
    # ---------------------------------------------------------------------
    prompt = f"""
    You are the Lead Fraud Analyst for an e-commerce platform.
    We have programmatically decided to take the following action on a product review: {decision}
    Scenario Triggered: {scenario_context}

    Context Data:
    - Visual Discrepancy Score (Catalog vs Unboxing): {variance:.2f} (Threshold is {VARIANCE_THRESHOLD})
    - Buyer Scam Intent Detected in Text: {scam_intent}
    - Seller Historical Trust Score: {trust_score}/100

    Write a single, highly professional sentence summarizing exactly why this action was taken.
    This will be displayed to human auditors. Do not use JSON, just return the raw sentence.
    """

    try:
        response = llm_exec.invoke([HumanMessage(content=prompt)])
        executive_summary = response.content.strip().strip('"')

    except Exception as e:
        print(f"⚠️ [EXECUTIVE NODE] LLM Summary Error: {e}")
        executive_summary = f"Programmatic action {decision} applied based on system thresholds."

    # Save the AI-generated summary to the telemetry log
    log_action = f"Executive Action: {decision}. Summary: {executive_summary}"
    state['agent_telemetry_logs'].append(log_action)

    print(f"🏁 [FINAL VERDICT] {decision} | {executive_summary}")
    return state