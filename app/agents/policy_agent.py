from langchain_core.messages import AIMessage
from app.agents.state import FinBotState
from app.services.rag import search
from app.agents.memory import build_context_with_memory
from app.services.redis_client import cache_rag_response, get_cached_rag_response
from app.services.llm import llm


def policy_agent_node(state: FinBotState) -> FinBotState:
    last_message = state["messages"][-1].content

    # Check Redis cache first
    cached = get_cached_rag_response(last_message)
    if cached:
        return {
            **state,
            "context": "cached",
            "response": cached,
            "messages": state["messages"] + [AIMessage(content=cached)]
        }

    # RAG search
    results = search(last_message, top_k=3)
    context = "\n".join([f"- {r['text']}" for r in results])

    messages = build_context_with_memory(state["messages"], state.get("summary", ""))
    messages.append({
        "role": "user",
        "content": f"""Relevant bank policies:
{context}

Answer the customer's question using only the above policies.
If not covered, say 'Please contact our support team for more details.'"""
    })

    response = llm.invoke(messages)

    # Cache response in Redis for 30 minutes
    cache_rag_response(last_message, response.content)

    return {
        **state,
        "context": context,
        "response": response.content,
        "messages": state["messages"] + [AIMessage(content=response.content)]
    }