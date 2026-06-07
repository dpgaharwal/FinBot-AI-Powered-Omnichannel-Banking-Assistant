from langchain_ollama import ChatOllama
from app.core.config import settings

llm = ChatOllama(model=settings.OLLAMA_MODEL)


def summarize_conversation(messages: list) -> str:
    if len(messages) < 4:
        return ""

    conversation = "\n".join([
        f"{m.type.upper()}: {m.content}"
        for m in messages[:-2]  # exclude last exchange
    ])

    prompt = f"""Summarize this banking conversation in 2-3 sentences. 
Focus on what the customer asked and what was resolved.

Conversation:
{conversation}

Summary:"""

    response = llm.invoke(prompt)
    return response.content


def build_context_with_memory(messages: list, summary: str) -> list:
    system_prompt = """You are FinBot, an AI banking assistant. 
You help customers with account balance, transactions, loans, policies, and disputes.
Be concise, accurate, and professional."""

    if summary:
        system_prompt += f"\n\nConversation summary so far:\n{summary}"

    from langchain_core.messages import SystemMessage
    return [SystemMessage(content=system_prompt)] + messages[-4:]  # last 2 exchanges