from twilio.rest import Client
from app.core.config import settings

client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)


def send_whatsapp_message(to: str, message: str) -> str:
    msg = client.messages.create(
        from_=settings.TWILIO_WHATSAPP_FROM,
        to=f"whatsapp:{to}",
        body=message
    )
    return msg.sid


def parse_whatsapp_webhook(form_data: dict) -> dict:
    return {
        "from": form_data.get("From", "").replace("whatsapp:", ""),
        "body": form_data.get("Body", ""),
        "message_sid": form_data.get("MessageSid", "")
    }