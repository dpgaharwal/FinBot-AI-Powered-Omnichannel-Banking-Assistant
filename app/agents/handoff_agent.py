from langchain_core.messages import AIMessage
from app.agents.state import FinBotState
from app.services.mcp_server import get_connection
import uuid
from datetime import datetime


def create_support_ticket(customer_email: str, issue: str) -> str:
    ticket_id = f"TKT{uuid.uuid4().hex[:8].upper()}"
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO audit_logs (id, user_id, action, details, outcome, created_at) VALUES (%s, %s, %s, %s, %s, %s)",
        (
            str(uuid.uuid4()),
            customer_email,
            "human_handoff",
            f"Ticket {ticket_id}: {issue}",
            "success",
            datetime.utcnow()
        )
    )
    conn.commit()
    cursor.close()
    conn.close()
    return ticket_id


def handoff_agent_node(state: FinBotState) -> FinBotState:
    customer_email = state.get("customer_email", "happy@finbot.com")
    last_message = state["messages"][-1].content

    ticket_id = create_support_ticket(customer_email, last_message)

    response = f"""I understand your concern and I'm connecting you to a human agent.

Your support ticket has been created: **{ticket_id}**

A banking specialist will reach out to you within 2-4 business hours on your registered contact.

Is there anything else I can help you with in the meantime?"""

    return {
        **state,
        "escalate": True,
        "response": response,
        "messages": state["messages"] + [AIMessage(content=response)]
    }