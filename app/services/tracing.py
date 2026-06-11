from langfuse import Langfuse
from app.core.config import settings
import time

langfuse = Langfuse(
    public_key=settings.LANGFUSE_PUBLIC_KEY,
    secret_key=settings.LANGFUSE_SECRET_KEY,
    host=settings.LANGFUSE_HOST
)


def trace_agent_call(
    user_id: str,
    session_id: str,
    input_text: str,
    output_text: str,
    intent: str,
    latency_ms: float,
    metadata: dict = {}
):
    trace = langfuse.trace(
        name="finbot_chat",
        user_id=user_id,
        session_id=session_id,
        input=input_text,
        output=output_text,
        metadata={
            "intent": intent,
            "latency_ms": round(latency_ms, 2),
            **metadata
        }
    )

    trace.span(
        name=f"agent:{intent}",
        input=input_text,
        output=output_text,
        metadata={"intent": intent}
    )

    langfuse.flush()
    return trace.id