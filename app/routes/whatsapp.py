from fastapi import APIRouter, Request, Response
from langchain_core.messages import HumanMessage
from app.agents.graph import finbot_graph
from app.services.whatsapp import send_whatsapp_message, parse_whatsapp_webhook
from app.services.audit import log_action

router = APIRouter()

# In-memory session store per phone number
sessions: dict = {}


@router.post("/webhook/whatsapp")
async def whatsapp_webhook(request: Request):
    form_data = await request.form()
    data = parse_whatsapp_webhook(dict(form_data))

    phone = data["from"]
    message = data["body"]

    if not message:
        return Response(content="", media_type="text/xml")

    # Get or create session for this phone number
    if phone not in sessions:
        sessions[phone] = {
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

    state = sessions[phone]
    state["messages"] = state["messages"] + [HumanMessage(content=message)]

    # Run through same LangGraph pipeline
    state = finbot_graph.invoke(state)
    sessions[phone] = state

    response_text = state.get("response", "Sorry, I could not process that.")
    intent = state.get("intent", "unknown")

    # Send reply via Twilio
    send_whatsapp_message(phone, response_text)

    return Response(content="", media_type="text/xml")