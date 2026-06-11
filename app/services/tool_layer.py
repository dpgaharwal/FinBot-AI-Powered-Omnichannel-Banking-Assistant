import mysql.connector
from mysql.connector import pooling
from app.core.config import settings

db_pool = mysql.connector.pooling.MySQLConnectionPool(
    pool_name="finbot_pool",
    pool_size=10,
    host=settings.MYSQL_HOST,
    port=settings.MYSQL_PORT,
    database=settings.MYSQL_DATABASE,
    user=settings.MYSQL_USER,
    password=settings.MYSQL_PASSWORD
)


def get_connection():
    return db_pool.get_connection()


def get_customer_by_email(email: str) -> dict:
    conn = get_connection()
    try:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute("SELECT * FROM customers WHERE email = %s", (email,))
            return cursor.fetchone() or {}
    finally:
        conn.close()


def get_accounts(customer_id: str) -> list:
    conn = get_connection()
    try:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute("SELECT * FROM accounts WHERE customer_id = %s", (customer_id,))
            return cursor.fetchall()
    finally:
        conn.close()


def get_transactions(account_id: str, limit: int = 5) -> list:
    conn = get_connection()
    try:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute(
                "SELECT * FROM transactions WHERE account_id = %s ORDER BY created_at DESC LIMIT %s",
                (account_id, limit)
            )
            return cursor.fetchall()
    finally:
        conn.close()


def get_loans(customer_id: str) -> list:
    conn = get_connection()
    try:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute("SELECT * FROM loans WHERE customer_id = %s", (customer_id,))
            return cursor.fetchall()
    finally:
        conn.close()


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