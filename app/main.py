import os
from dotenv import load_dotenv

load_dotenv()

os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGSMITH_API_KEY", "")
os.environ["LANGCHAIN_PROJECT"] = os.getenv("LANGSMITH_PROJECT", "finbot")
os.environ["LANGCHAIN_TRACING_V2"] = os.getenv("LANGCHAIN_TRACING_V2", "false")
os.environ["LANGCHAIN_ENDPOINT"] = os.getenv("LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com")

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from slowapi.errors import RateLimitExceeded
from app.routes.chat import router as chat_router
from app.routes.whatsapp import router as whatsapp_router
from app.middleware.rate_limit import limiter
from app.core.config import settings
from app.services.events import consume_emi_paid_events
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import asyncio
import threading
import time


async def handle_emi_notification(payload: dict):
    customer_id = payload.get("customer_id")
    message = payload.get("message")
    print(f"EMI Notification → customer: {customer_id} | {message}")


def start_consumer_thread():
    while True:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            print("RabbitMQ consumer starting...")
            loop.run_until_complete(consume_emi_paid_events(handle_emi_notification))
        except Exception as e:
            print(f"RabbitMQ consumer failed, retrying in 5s: {e}")
            time.sleep(5)
        finally:
            loop.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    thread = threading.Thread(target=start_consumer_thread, daemon=True)
    thread.start()
    print("RabbitMQ consumer started.")
    yield


app = FastAPI(title="FinBot", version="1.0.0", lifespan=lifespan)

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/chat")
async def chat_ui():
    return FileResponse("static/index.html")

app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"error": "Too many requests. Please slow down."}
    )


app.include_router(chat_router, prefix="/api/v1")
app.include_router(whatsapp_router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {"status": "ok", "model": settings.OLLAMA_MODEL}


@app.get("/")
async def root():
    return {
        "app": "FinBot",
        "version": "1.0.0",
        "compliance": "RBI/PCI-DSS aligned",
        "status": "operational"
    }