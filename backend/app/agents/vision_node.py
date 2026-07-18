import os
import json
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from app.agents.state import ProductEvaluationState

# Fetch the key regardless of whether you named it GEMINI_API_KEY or GOOGLE_API_KEY
api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

# Initialize Gemini 3.5 Flash (Lightning fast and excellent at vision QA)
vision_llm = ChatGoogleGenerativeAI(
    model="gemini-3.5-flash",
    api_key=api_key,
    temperature=0.0
)

def analyze_vision(state: ProductEvaluationState) -> ProductEvaluationState:
    """
    The Vision Node: Multimodal Quality Assurance via Gemini.
    Uses an LLM to visually inspect the unboxing image for material degradation or knockoffs.
    """
    print(f"👁️ [VISION NODE] Running Gemini Multimodal Analysis for: {state['review_id']}")
    expected_product = state.get('product_name', 'Expected Product')
    catalog_image = state.get('catalog_image_url', '')
    unboxing_image = state.get('unboxing_image_url', '')

    # We ask Gemini to act as a QA inspector, looking at the image and the complaint
    prompt = f"""
    You are an expert e-commerce quality assurance AI.
    You are provided with TWO images below:
    1. The first image is the OFFICIAL CATALOG IMAGE of the product ("{expected_product}").
    2. The second image is the UNBOXING IMAGE uploaded by the buyer.

    The buyer's review text is: "{state.get('review_text', '')}"

    TASK: Perform a strict Image-to-Image comparison.
    Does the Unboxing Image show the exact same item (matching materials, quality, brand, and build) as the Catalog Image?
    Or does it show a 'Bait & Switch' (e.g., cheap knockoff, different material, completely different item)?

    Respond ONLY with a valid JSON object in this exact format:
    {{"visual_discrepancy_score": 0.0 to 1.0, "reason": "short explanation comparing the two images"}}
    """

    try:
        # Pass both the text prompt and the image URL to Gemini
        message = HumanMessage(
            content=[
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": catalog_image}},
                {"type": "image_url", "image_url": {"url": unboxing_image}}
            ]
        )

        response = vision_llm.invoke([message])
        print("\n🔍 --- GEMINI RAW RESPONSE DEBUG ---")
        print(f"Type of response.content: {type(response.content)}")
        print(f"Value of response.content: {response.content}")
        print("-----------------------------------\n")

        if isinstance(response.content, list) and len(response.content) > 0:
            first_block = response.content[0]
            if isinstance(first_block, dict) and 'text' in first_block:
                raw_content = first_block['text']
            else:
                raw_content = str(first_block)
        elif isinstance(response.content, str):
            raw_content = response.content
        else:
            raw_content = str(response.content)

        # Clean and parse the JSON output
        raw_content = raw_content.strip().strip("`").removeprefix("json").strip()
        result = json.loads(raw_content)

        score = float(result.get("visual_discrepancy_score", 0.0))
        reason = result.get("reason", "Analysis successful.")

        state['visual_discrepancy_score'] = score
        state['vision_notes'] = f"Gemini Multimodal: {reason}"

        print(f"👁️ [VISION NODE] Gemini Score: {score} | Reason: {reason}")

    except Exception as e:
        print(f"⚠️ [VISION NODE] Gemini Error: {e}")
        state['visual_discrepancy_score'] = 0.0
        state['vision_notes'] = f"Vision AI failed: {str(e)}"

    # Return only the keys this node updates
    return {
        "visual_discrepancy_score": state.get('visual_discrepancy_score', 0.0),
        "vision_notes": state.get('vision_notes', '')
    }