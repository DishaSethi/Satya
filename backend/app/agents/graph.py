from langgraph.graph import StateGraph, START, END
from app.agents.state import ProductEvaluationState
from app.agents.pulse_node import analyze_text
from app.agents.vision_node import analyze_vision
from app.agents.executive_node import make_final_decision

workflow = StateGraph(ProductEvaluationState)

workflow.add_node("pulse_agent", analyze_text)
workflow.add_node("vision_agent", analyze_vision)
workflow.add_node("executive_agent", make_final_decision)

# FAN-OUT: Start both Pulse and Vision at the exact same time (Parallel)
workflow.add_edge(START, "pulse_agent")
workflow.add_edge(START, "vision_agent")

# FAN-IN: Executive Agent waits for BOTH to finish before starting
workflow.add_edge(["pulse_agent", "vision_agent"], "executive_agent")

workflow.add_edge("executive_agent", END)

swarm_app = workflow.compile()