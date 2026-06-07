import os
from dotenv import load_dotenv

load_dotenv()

os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGSMITH_API_KEY")
os.environ["LANGCHAIN_PROJECT"] = os.getenv("LANGSMITH_PROJECT")
os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"

from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.routes.chat import router as chat_router
from app.routes.whatsapp import router as whatsapp_router
from app.core.config import settings
from app.services.events import consume_emi_paid_events
import asyncio
import threading


async def handle_emi_notification(payload: dict):
    customer_id = payload.get("customer_id")
    message = payload.get("message")
    print(f"📱 EMI Notification → customer: {customer_id} | {message}")
    # Production: lookup phone from DB → send_whatsapp_message(phone, message)


def start_consumer_thread():
    """Run RabbitMQ consumer in a separate thread with its own event loop."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(consume_emi_paid_events(handle_emi_notification))
    except Exception as e:
        print(f"Consumer thread error: {e}")
    finally:
        loop.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start RabbitMQ consumer in background thread
    thread = threading.Thread(target=start_consumer_thread, daemon=True)
    thread.start()
    print("RabbitMQ consumer started.")
    yield


app = FastAPI(title="FinBot", version="1.0.0", lifespan=lifespan)

app.include_router(chat_router, prefix="/api/v1")
app.include_router(whatsapp_router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {"status": "ok", "model": settings.OLLAMA_MODEL}