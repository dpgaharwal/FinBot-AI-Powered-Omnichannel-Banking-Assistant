import os
from dotenv import load_dotenv

load_dotenv()

os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGSMITH_API_KEY")
os.environ["LANGCHAIN_PROJECT"] = os.getenv("LANGSMITH_PROJECT")
os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"

from fastapi import FastAPI
from app.routes.chat import router as chat_router
from app.routes.whatsapp import router as whatsapp_router
from app.core.config import settings

app = FastAPI(title="FinBot", version="1.0.0")

app.include_router(chat_router, prefix="/api/v1")
app.include_router(whatsapp_router, prefix="/api/v1")

@app.get("/health")
async def health():
    return {"status": "ok", "model": settings.OLLAMA_MODEL}