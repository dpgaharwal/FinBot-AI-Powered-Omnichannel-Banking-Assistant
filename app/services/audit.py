import uuid
from datetime import datetime
from app.services.mcp_server import get_connection


def log_action(user_id: str, action: str, details: str, outcome: str = "success"):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO audit_logs (id, user_id, action, details, outcome, created_at) VALUES (%s, %s, %s, %s, %s, %s)",
            (
                str(uuid.uuid4()),
                user_id,
                action,
                details,
                outcome,
                datetime.utcnow()
            )
        )
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Audit log failed: {e}")