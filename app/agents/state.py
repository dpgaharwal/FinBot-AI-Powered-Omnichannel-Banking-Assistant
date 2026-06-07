from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages


class FinBotState(TypedDict):
    messages: Annotated[list, add_messages]
    intent: str
    customer_email: str
    customer_data: dict
    account_data: list
    context: str
    response: str
    escalate: bool
    summary: str