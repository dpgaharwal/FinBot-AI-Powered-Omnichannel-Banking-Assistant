from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, HTTPException
from langchain_core.messages import HumanMessage
from app.agents.graph import finbot_graph
from app.middleware.auth import verify_token
from app.services.audit import log_action
from app.services.guardrails import sanitize_input, sanitize_output
import asyncio

router = APIRouter()

active_connections: dict[str, list[WebSocket]] = {}


async def broadcast_to_user(user: str, message: str):
    if user in active_connections:
        for ws in active_connections[user]:
            try:
                await ws.send_text(message)
            except:
                pass


@router.post("/token")
async def get_token():
    from app.middleware.auth import create_access_token
    token = create_access_token(data={"sub": "user_happy"})
    return {"access_token": token, "token_type": "bearer"}


@router.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket, token: str = Query(...)):
    try:
        payload = verify_token(token)
        user = payload.get("sub")
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
        "customer_email": "happy@finbot.com",
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
                    details=f"Blocked message: {user_message[:100]}",
                    outcome="failure"
                )
                continue

            await broadcast_to_user(user, "[TYPING:true]")

            state["messages"] = state["messages"] + [HumanMessage(content=sanitized)]

            state = finbot_graph.invoke(state)

            response = state.get("response", "I'm sorry, I could not process that.")
            intent = state.get("intent", "unknown")

            # Guardrail — sanitize output
            safe_response = sanitize_output(response)

            log_action(
                user_id=user,
                action=f"intent:{intent}",
                details=f"Q: {user_message[:100]} | A: {safe_response[:100]}",
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