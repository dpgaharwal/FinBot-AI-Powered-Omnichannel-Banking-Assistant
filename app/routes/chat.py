from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, HTTPException
from langchain_core.messages import HumanMessage
from app.agents.graph import finbot_graph
from app.middleware.auth import verify_token
from app.services.audit import log_action
import asyncio

router = APIRouter()

# Multi-device session store: user -> list of active websockets
active_connections: dict[str, list[WebSocket]] = {}


async def broadcast_to_user(user: str, message: str):
    """Send message to all active devices for a user."""
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

    # Multi-device: register this connection
    if user not in active_connections:
        active_connections[user] = []
    active_connections[user].append(websocket)

    # Notify all devices this user is online
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

            # Typing indicator to all devices
            await broadcast_to_user(user, "[TYPING:true]")

            state["messages"] = state["messages"] + [HumanMessage(content=user_message)]

            # Run LangGraph
            state = finbot_graph.invoke(state)

            response = state.get("response", "I'm sorry, I could not process that.")
            intent = state.get("intent", "unknown")

            # Audit log
            log_action(
                user_id=user,
                action=f"intent:{intent}",
                details=f"Q: {user_message[:100]} | A: {response[:100]}",
                outcome="success"
            )

            # Stop typing indicator
            await broadcast_to_user(user, "[TYPING:false]")
            await broadcast_to_user(user, f"[INTENT:{intent}]")
            await broadcast_to_user(user, response)
            await broadcast_to_user(user, "[END]")

    except WebSocketDisconnect:
        active_connections[user].remove(websocket)
        if not active_connections[user]:
            del active_connections[user]
            await broadcast_to_user(user, "[STATUS:offline]")
        print(f"User {user} disconnected")