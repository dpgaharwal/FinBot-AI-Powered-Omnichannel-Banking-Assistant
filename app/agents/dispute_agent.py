from langchain_ollama import ChatOllama
from langchain_core.messages import AIMessage
from app.agents.state import FinBotState
from app.services.mcp_server import execute_mcp_tool
from app.services.rag import search
from app.agents.memory import build_context_with_memory
from app.core.config import settings

llm = ChatOllama(model=settings.OLLAMA_MODEL)


def dispute_agent_node(state: FinBotState) -> FinBotState:
    customer_email = state.get("customer_email", "happy@finbot.com")
    last_message = state["messages"][-1].content

    # MCP — get recent transactions
    customer = execute_mcp_tool("get_customer_by_email", {"email": customer_email})
    accounts = execute_mcp_tool("get_accounts", {"customer_id": customer.get("id", "c1")})

    txn_summary = ""
    if accounts:
        txns = execute_mcp_tool("get_transactions", {"account_id": accounts[0]["id"], "limit": 5})
        txn_summary = "\n".join([
            f"- {t['type'].upper()} Rs.{t['amount']} | {t['description']} | {t['status']} | {t['created_at']}"
            for t in txns
        ])

    # RAG — get dispute/refund policies
    results = search(last_message, top_k=2)
    policy_context = "\n".join([f"- {r['text']}" for r in results])

    messages = build_context_with_memory(state["messages"], state.get("summary", ""))
    messages.append({
        "role": "user",
        "content": f"""Customer: {customer.get('name')}

Recent Transactions:
{txn_summary}

Relevant Policies:
{policy_context}

Help the customer resolve their dispute or refund issue using above data.
If unresolvable, suggest escalation to human agent."""
    })

    response = llm.invoke(messages)

    return {
        **state,
        "context": policy_context,
        "response": response.content,
        "messages": state["messages"] + [AIMessage(content=response.content)]
    }