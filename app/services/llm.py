import httpx
import json
from app.core.config import settings
from langchain_ollama import ChatOllama

# Shared LLM singleton — all agents use this
llm = ChatOllama(model=settings.OLLAMA_MODEL)


async def stream_ollama_response(messages: list[dict]):
    url = f"{settings.OLLAMA_BASE_URL}/api/chat"
    payload = {
        "model": settings.OLLAMA_MODEL,
        "messages": messages,
        "stream": True
    }

    full_response = ""
    async with httpx.AsyncClient(timeout=120) as client:
        async with client.stream("POST", url, json=payload) as response:
            async for line in response.aiter_lines():
                if line:
                    data = json.loads(line)
                    token = data.get("message", {}).get("content", "")
                    if token:
                        full_response += token
                        yield token
                    if data.get("done"):
                        break