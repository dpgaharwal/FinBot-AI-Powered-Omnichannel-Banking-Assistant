from langchain_ollama import ChatOllama
from langchain_core.messages import AIMessage
from app.agents.state import FinBotState
from app.services.mcp_server import execute_mcp_tool
from app.agents.memory import build_context_with_memory
from app.core.config import settings

llm = ChatOllama(model=settings.OLLAMA_MODEL)


def balance_agent_node(state: FinBotState) -> FinBotState:
    customer_email = state.get("customer_email")
    if not customer_email:
        return {
            **state,
            "response": "Authentication required. Please log in to access account information.",
            "messages": state["messages"] + [AIMessage(content="Authentication required. Please log in to access account information.")]
        }
    
    # MCP calls
    customer = execute_mcp_tool("get_customer_by_email", {"email": customer_email})
    accounts = execute_mcp_tool("get_accounts", {"customer_id": customer.get("id", "c1")})

    # Build context
    account_summary = "\n".join([
        f"- {a['account_type'].upper()} ({a['account_number']}): Rs. {a['balance']} [{a['status']}]"
        for a in accounts
    ])

    messages = build_context_with_memory(state["messages"], state.get("summary", ""))
    messages.append({
        "role": "user",
        "content": f"""Customer: {customer.get('name')} | KYC: {customer.get('kyc_status')}
Accounts:
{account_summary}

Answer the customer's question about their account/balance using above data."""
    })

    response = llm.invoke(messages)

    return {
        **state,
        "customer_data": customer,
        "account_data": accounts,
        "response": response.content,
        "messages": state["messages"] + [AIMessage(content=response.content)]
    }