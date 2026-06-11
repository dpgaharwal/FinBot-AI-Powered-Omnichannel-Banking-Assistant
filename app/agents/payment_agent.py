from langchain_core.messages import AIMessage
from app.agents.state import FinBotState
from app.services.payment import create_emi_order, record_emi_payment, get_loan_details
from app.services.events import publish_emi_paid_event
from app.services.audit import log_action
from app.services.redis_client import set_idempotency_key, get_idempotency_key
from app.services.llm import llm
import asyncio
import concurrent.futures


def payment_agent_node(state: FinBotState) -> FinBotState:
    customer_email = state.get("customer_email")
    if not customer_email:
        response = "Authentication required. Please log in to access payment information."
        return {
            **state,
            "response": response,
            "messages": state["messages"] + [AIMessage(content=response)]
        }

    customer_data = state.get("customer_data", {})
    customer_id = customer_data.get("id")

    # If customer_data not populated yet fetch it
    if not customer_id:
        from app.services.tool_layer import execute_mcp_tool
        customer = execute_mcp_tool("get_customer_by_email", {"email": customer_email})
        customer_id = customer.get("id")

    if not customer_id:
        response = "Could not find your account. Please contact support."
        return {
            **state,
            "response": response,
            "messages": state["messages"] + [AIMessage(content=response)]
        }

    loans = get_loan_details(customer_id)

    if not loans:
        response = "You have no active loans at the moment."
        return {
            **state,
            "response": response,
            "messages": state["messages"] + [AIMessage(content=response)]
        }

    loan = loans[0]
    loan_id = loan["id"]
    emi_amount = float(loan["emi_amount"])
    remaining = loan["remaining_emis"]
    loan_type = loan["loan_type"]

    # Idempotency check — prevent duplicate EMI payments
    idempotency_key = f"{customer_id}:{loan_id}:{remaining}"
    existing = get_idempotency_key(idempotency_key)
    if existing:
        response = f"Your EMI payment for this month has already been processed. Transaction ID: {existing}"
        return {
            **state,
            "response": response,
            "messages": state["messages"] + [AIMessage(content=response)]
        }

    try:
        order = create_emi_order(customer_id, loan_id, emi_amount)
        order_id = order.get("id", f"order_{loan_id}")

        txn_id = record_emi_payment(loan_id, customer_id, emi_amount, order_id)

        # Store idempotency key — expires in 24 hours
        set_idempotency_key(idempotency_key, txn_id)

        # Publish event in separate thread
        with concurrent.futures.ThreadPoolExecutor() as pool:
            pool.submit(
                asyncio.run,
                publish_emi_paid_event(customer_id, loan_id, emi_amount, txn_id)
            )

        log_action(
            user_id=customer_email,
            action="emi_payment",
            details=f"Loan {loan_id} | EMI ₹{emi_amount} | Order {order_id} | Txn {txn_id}",
            outcome="success"
        )

        response = f"""✅ EMI Payment Processed Successfully!

**Loan Type:** {loan_type.upper()}
**EMI Amount:** ₹{emi_amount:,.2f}
**Razorpay Order ID:** {order_id}
**Transaction ID:** {txn_id}
**Remaining EMIs:** {remaining - 1}

Your payment has been recorded and a confirmation notification has been sent."""

    except Exception as e:
        log_action(
            user_id=customer_email,
            action="emi_payment",
            details=f"Failed: {str(e)}",
            outcome="failure"
        )
        response = f"I encountered an issue processing your EMI payment. Please try again or contact support. Error: {str(e)}"

    return {
        **state,
        "response": response,
        "messages": state["messages"] + [AIMessage(content=response)]
    }