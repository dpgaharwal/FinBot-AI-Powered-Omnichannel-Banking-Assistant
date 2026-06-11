import razorpay
from app.core.config import settings
from app.services.tool_layer import get_connection
from datetime import datetime
import uuid

client = razorpay.Client(
    auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
)


def create_emi_order(customer_id: str, loan_id: str, emi_amount: float) -> dict:
    """Create a Razorpay order for EMI payment."""
    order_data = {
        "amount": int(emi_amount * 100),  # Razorpay uses paise
        "currency": "INR",
        "receipt": f"emi_{loan_id}_{uuid.uuid4().hex[:8]}",
        "notes": {
            "customer_id": customer_id,
            "loan_id": loan_id,
            "type": "emi_payment"
        }
    }
    order = client.order.create(data=order_data)
    return order


def record_emi_payment(loan_id: str, customer_id: str, amount: float, order_id: str) -> str:
    txn_id = str(uuid.uuid4())
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO transactions (id, account_id, type, amount, description, status, created_at)
               SELECT %s, a.id, 'debit', %s, %s, 'success', %s
               FROM accounts a WHERE a.customer_id = %s LIMIT 1""",
            (
                txn_id,
                amount,
                f"EMI payment for loan {loan_id} | Order {order_id}",
                datetime.utcnow(),
                customer_id
            )
        )
        cursor.execute(
            "UPDATE loans SET remaining_emis = remaining_emis - 1 WHERE id = %s",
            (loan_id,)
        )
        conn.commit()
        cursor.close()
        return txn_id
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def get_loan_details(customer_id: str) -> list:
    """Get active loans for customer."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT * FROM loans WHERE customer_id = %s AND status = 'active'",
        (customer_id,)
    )
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    return result