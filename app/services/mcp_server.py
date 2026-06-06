import mysql.connector
from app.core.config import settings


def get_connection():
    return mysql.connector.connect(
        host=settings.MYSQL_HOST,
        port=settings.MYSQL_PORT,
        database=settings.MYSQL_DATABASE,
        user=settings.MYSQL_USER,
        password=settings.MYSQL_PASSWORD
    )


def get_customer_by_email(email: str) -> dict:
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM customers WHERE email = %s", (email,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result or {}


def get_accounts(customer_id: str) -> list:
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM accounts WHERE customer_id = %s", (customer_id,))
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    return result


def get_transactions(account_id: str, limit: int = 5) -> list:
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT * FROM transactions WHERE account_id = %s ORDER BY created_at DESC LIMIT %s",
        (account_id, limit)
    )
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    return result


def get_loans(customer_id: str) -> list:
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM loans WHERE customer_id = %s", (customer_id,))
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    return result


# MCP tool registry — LLM calls these by name
MCP_TOOLS = {
    "get_customer_by_email": get_customer_by_email,
    "get_accounts": get_accounts,
    "get_transactions": get_transactions,
    "get_loans": get_loans,
}


def execute_mcp_tool(tool_name: str, params: dict) -> dict | list:
    if tool_name not in MCP_TOOLS:
        return {"error": f"Unknown tool: {tool_name}"}
    return MCP_TOOLS[tool_name](**params)