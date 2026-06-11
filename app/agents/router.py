from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage
from app.agents.state import FinBotState
from app.core.config import settings
from app.services.llm import llm



INTENT_PROMPT = """You are an intent classifier for a banking assistant.
Classify the user's message into exactly one of these intents:
- balance: asking about account balance or account details
- transactions: asking about transaction history or recent payments
- policy: asking about bank rules, fees, limits, or procedures
- dispute: asking about refunds, failed transactions, or raising a complaint
- loan: asking about loans or EMI
- handoff: user is angry, wants human agent, or issue is complex
- general: anything else

Respond with only the intent word, nothing else.

User message: {message}
Intent:"""


def router_node(state: FinBotState) -> FinBotState:
    last_message = state["messages"][-1].content
    prompt = INTENT_PROMPT.format(message=last_message)
    response = llm.invoke(prompt)
    intent = response.content.strip().lower()

    valid_intents = ["balance", "transactions", "policy", "dispute", "loan", "handoff", "general"]
    if intent not in valid_intents:
        intent = "general"

    return {**state, "intent": intent}