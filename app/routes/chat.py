from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, HTTPException
from app.services.llm import stream_ollama_response, traced_chat
from app.middleware.auth import verify_token
import asyncio

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
    conversation_history = []

    try:
        while True:
            user_message = await websocket.receive_text()

            conversation_history.append({
                "role": "user",
                "content": user_message
            })

            full_response = ""

            # Stream to websocket
            async for token_chunk in stream_ollama_response(conversation_history):
                full_response += token_chunk
                await websocket.send_text(token_chunk)

            conversation_history.append({
                "role": "assistant",
                "content": full_response
            })

            await websocket.send_text("[END]")

            # Send to LangSmith as a trace (non-blocking)
            asyncio.create_task(traced_chat(conversation_history))

    except WebSocketDisconnect:
        print(f"User {user} disconnected")