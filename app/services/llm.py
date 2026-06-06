import httpx
import json
from langsmith import traceable
from app.core.config import settings


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


@traceable(name="finbot_chat", run_type="llm")
async def traced_chat(messages: list[dict]) -> str:
    full_response = ""
    async for token in stream_ollama_response(messages):
        full_response += token
    return full_response