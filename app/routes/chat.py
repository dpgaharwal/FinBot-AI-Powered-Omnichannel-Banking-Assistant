from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, HTTPException
from langchain_core.messages import HumanMessage
from app.agents.graph import finbot_graph
from app.middleware.auth import verify_token

router = APIRouter()


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

            state["messages"] = state["messages"] + [HumanMessage(content=user_message)]

            result = await websocket.send_text("⏳ Thinking...")

            state = finbot_graph.invoke(state)

            response = state.get("response", "I'm sorry, I could not process that.")
            intent = state.get("intent", "unknown")

            await websocket.send_text(f"[INTENT:{intent}]")
            await websocket.send_text(response)
            await websocket.send_text("[END]")

    except WebSocketDisconnect:
        print(f"User {user} disconnected")