from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, HTTPException, Depends, Request
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from langchain_core.messages import HumanMessage
from app.agents.graph import finbot_graph
from app.middleware.auth import verify_token
from app.services.audit import log_action
from app.services.guardrails import sanitize_input, sanitize_output
from app.middleware.rate_limit import limiter
from app.services.tracing import trace_agent_call
import time
import asyncio
import secrets

router = APIRouter()

security = HTTPBasic()

# Demo users - in production this comes from DB / Firebase
DEMO_USERS = {
    "happy@finbot.com": {"password": "finbot123", "customer_id": "c1"},
    "priya@finbot.com": {"password": "finbot123", "customer_id": "c2"},
    "rahul@finbot.com": {"password": "finbot123", "customer_id": "c3"},
}

active_connections: dict[str, list[WebSocket]] = {}


async def broadcast_to_user(user: str, message: str):
    if user in active_connections:
        for ws in active_connections[user]:
            try:
                await ws.send_text(message)
            except Exception as e:
                print(f"WebSocket send failed for user {user}: {e}")


@router.post("/token")
async def get_token(credentials: HTTPBasicCredentials = Depends(security)):
    user = DEMO_USERS.get(credentials.username)
    if not user or not secrets.compare_digest(credentials.password, user["password"]):
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"}
        )
    from app.middleware.auth import create_access_token
    token = create_access_token(data={
        "sub": credentials.username,
        "customer_id": user["customer_id"]
    })
    return {"access_token": token, "token_type": "bearer"}


@router.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket, token: str = Query(...)):
    try:
        payload = verify_token(token)
        user = payload.get("sub")
        customer_id = payload.get("customer_id", "c1")
    except HTTPException:
        await websocket.close(code=1008)
        return

    await websocket.accept()

    if user not in active_connections:
        active_connections[user] = []
    active_connections[user].append(websocket)

    await broadcast_to_user(user, "[STATUS:online]")

    state = {
        "messages": [],
        "intent": "",
        "customer_email": user,
        "customer_data": {},
        "account_data": [],
        "context": "",
        "response": "",
        "escalate": False,
        "summary": ""
    }

    try:
        while True:
            user_message = await websocket.receive_text()

            # Guardrail — sanitize input
            is_safe, sanitized = sanitize_input(user_message)
            if not is_safe:
                await broadcast_to_user(user, sanitized)
                await broadcast_to_user(user, "[END]")
                log_action(
                    user_id=user,
                    action="blocked:injection",
                    details=f"Blocked message: {sanitize_output(user_message[:100])}",
                    outcome="failure"
                )
                continue

            await broadcast_to_user(user, "[TYPING:true]")

            state["messages"] = state["messages"] + [HumanMessage(content=sanitized)]

            # Track latency
            start_time = time.time()
            state = await asyncio.to_thread(finbot_graph.invoke, state)
            latency_ms = (time.time() - start_time) * 1000

            response = state.get("response", "I'm sorry, I could not process that.")
            intent = state.get("intent", "unknown")

            # Guardrail — sanitize output
            safe_response = sanitize_output(response)
            masked_question = sanitize_output(user_message[:100])

            # Trace to LangFuse
            trace_agent_call(
                user_id=user,
                session_id=f"{user}_{id(websocket)}",
                input_text=masked_question,
                output_text=safe_response[:200],
                intent=intent,
                latency_ms=latency_ms
            )

            log_action(
                user_id=user,
                action=f"intent:{intent}",
                details=f"Q: {masked_question} | A: {safe_response[:100]}",
                outcome="success"
            )

            await broadcast_to_user(user, "[TYPING:false]")
            await broadcast_to_user(user, f"[INTENT:{intent}]")
            await broadcast_to_user(user, safe_response)
            await broadcast_to_user(user, "[END]")

    except WebSocketDisconnect:
        active_connections[user].remove(websocket)
        if not active_connections[user]:
            del active_connections[user]
        print(f"User {user} disconnected")