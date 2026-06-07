from langgraph.graph import StateGraph, END
from app.agents.state import FinBotState
from app.agents.router import router_node
from app.agents.balance_agent import balance_agent_node
from app.agents.policy_agent import policy_agent_node
from app.agents.dispute_agent import dispute_agent_node
from app.agents.handoff_agent import handoff_agent_node
from app.agents.payment_agent import payment_agent_node
from app.agents.memory import summarize_conversation


def should_route(state: FinBotState) -> str:
    intent = state.get("intent", "general")
    if intent in ["balance", "transactions"]:
        return "balance"
    elif intent == "policy":
        return "policy"
    elif intent == "dispute":
        return "dispute"
    elif intent == "loan":
        return "payment"
    elif intent == "handoff":
        return "handoff"
    else:
        return "policy"


def memory_node(state: FinBotState) -> FinBotState:
    messages = state.get("messages", [])
    existing_summary = state.get("summary", "")

    if len(messages) >= 6:
        summary = summarize_conversation(messages)
    else:
        summary = existing_summary

    return {**state, "summary": summary}


def build_graph():
    graph = StateGraph(FinBotState)

    # Add nodes
    graph.add_node("memory", memory_node)
    graph.add_node("router", router_node)
    graph.add_node("balance", balance_agent_node)
    graph.add_node("policy", policy_agent_node)
    graph.add_node("dispute", dispute_agent_node)
    graph.add_node("handoff", handoff_agent_node)
    graph.add_node("payment", payment_agent_node)

    # Entry point
    graph.set_entry_point("memory")

    # Edges
    graph.add_edge("memory", "router")
    graph.add_conditional_edges("router", should_route, {
        "balance": "balance",
        "policy": "policy",
        "dispute": "dispute",
        "handoff": "handoff",
        "payment": "payment"
    })

    graph.add_edge("balance", END)
    graph.add_edge("policy", END)
    graph.add_edge("dispute", END)
    graph.add_edge("handoff", END)
    graph.add_edge("payment", END)

    return graph.compile()


finbot_graph = build_graph()