from fastapi import APIRouter, Request, Response, HTTPException
from langchain_core.messages import HumanMessage
from app.agents.graph import finbot_graph
from app.services.whatsapp import send_whatsapp_message, parse_whatsapp_webhook
from app.services.audit import log_action
from app.services.guardrails import sanitize_input, sanitize_output
from app.middleware.rate_limit import limiter
from twilio.request_validator import RequestValidator
from app.core.config import settings
import asyncio

router = APIRouter()
sessions: dict = {}


def validate_twilio_request(request: Request, form_data: dict) -> bool:
    validator = RequestValidator(settings.TWILIO_AUTH_TOKEN)
    url = str(request.url)
    signature = request.headers.get("X-Twilio-Signature", "")
    return validator.validate(url, form_data, signature)


@router.post("/webhook/whatsapp")
@limiter.limit("30/minute")
async def whatsapp_webhook(request: Request):
    form_data = await request.form()
    form_dict = dict(form_data)

    if not validate_twilio_request(request, form_dict):
        raise HTTPException(status_code=403, detail="Invalid Twilio signature")

    data = parse_whatsapp_webhook(form_dict)
    phone = data["from"]
    message = data["body"]

    if not message:
        return Response(content="", media_type="text/xml")

    is_safe, sanitized = sanitize_input(message)
    if not is_safe:
        send_whatsapp_message(phone, "I cannot process that request.")
        return Response(content="", media_type="text/xml")

    if phone not in sessions:
        sessions[phone] = {
            "messages": [],
            "intent": "",
            "customer_email": f"{phone}@whatsapp.finbot.com",
            "customer_data": {},
            "account_data": [],
            "context": "",
            "response": "",
            "escalate": False,
            "summary": ""
        }

    state = sessions[phone]
    state["messages"] = state["messages"] + [HumanMessage(content=sanitized)]

    state = await asyncio.to_thread(finbot_graph.invoke, state)
    sessions[phone] = state

    response_text = state.get("response", "Sorry, I could not process that.")
    safe_response = sanitize_output(response_text)

    log_action(
        user_id=phone,
        action=f"whatsapp:{state.get('intent', 'unknown')}",
        details=f"Q: {sanitize_output(message[:100])} | A: {safe_response[:100]}",
        outcome="success"
    )

    send_whatsapp_message(phone, safe_response)
    return Response(content="", media_type="text/xml")