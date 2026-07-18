import os
import json
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
from app.agents.state import ProductEvaluationState


llm_text = ChatGroq(
    model="llama-3.1-8b-instant",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.0
)

def analyze_text(state: ProductEvaluationState) -> ProductEvaluationState:
    """
    The Pulse Node: Linguistic Deception Matrix.
    Analyzes buyer review text for structural indicators of fraud.
    """
    print(f"📝 [PULSE NODE] Analyzing review text for: {state['review_id']}")


    prompt = f"""
    You are an expert fraud detection AI analyzing an e-commerce product review.

    Review Text: "{state.get('review_text', '')}"

    TASK: We are looking for "Malicious Buyer Intent", "Competitor Review Bombing", OR severe "Scam Claims".
    Does this text look like a highly exaggerated, spammy, or malicious attack designed to ruin a seller's reputation? Or does it explicitly accuse the seller of a scam/fraud? (e.g., using words like "scam", "garbage", "fake", ALL CAPS).

    Differentiate this from generic dissatisfaction (e.g., "shipping was slow", "didn't fit"). If they aggressively accuse the product of being a fake/scam or use malicious attack language, flag scam_intent_detected as true.

    Respond ONLY in JSON format:
    {{"sentiment": "POSITIVE" | "NEUTRAL" | "NEGATIVE", "scam_intent_detected": true/false, "reason": "1 sentence explanation"}}
    """

    try:
        # Fixed the syntax error here (was response: llm_text.invoke)
        response = llm_text.invoke([HumanMessage(content=prompt)])

        raw_content = response.content.strip().strip("`").removeprefix("json").strip()
        result = json.loads(raw_content)

        state['text_sentiment'] = result.get('sentiment', 'NEUTRAL')
        state['scam_intent_detected'] = result.get('scam_intent_detected', False)
        state['pulse_notes'] = result.get('reason', 'Analysis successful.')



    except Exception as e:
        print(f"⚠️ [PULSE NODE] Error: {e}")
        state['text_sentiment'] = "NEUTRAL"
        state['scam_intent_detected'] = False
        state['pulse_notes'] = f"Agent failed to parse: {str(e)}"


    # Only return the keys this specific node is responsible for updating
    return {
        "text_sentiment": state.get('text_sentiment', 'NEUTRAL'),
        "pulse_notes": state.get('pulse_notes', ''),
        "scam_intent_detected": state.get('scam_intent_detected', False),

    }