import aio_pika
import json
from app.core.config import settings


async def publish_event(event_type: str, payload: dict):
    """Publish an event to RabbitMQ."""
    try:
        connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
        async with connection:
            channel = await connection.channel()
            queue = await channel.declare_queue(event_type, durable=True)
            message = aio_pika.Message(
                body=json.dumps(payload).encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT
            )
            await channel.default_exchange.publish(
                message,
                routing_key=event_type
            )
            print(f"Event published: {event_type} | {payload}")
    except Exception as e:
        print(f"Event publish failed: {e}")


async def publish_emi_paid_event(customer_id: str, loan_id: str, amount: float, txn_id: str):
    """EMI Paid → publish event → notification service picks it up."""
    await publish_event("emi.paid", {
        "customer_id": customer_id,
        "loan_id": loan_id,
        "amount": amount,
        "txn_id": txn_id,
        "message": f"Your EMI payment of ₹{amount} has been processed successfully. Transaction ID: {txn_id}"
    })


async def consume_emi_paid_events(notification_callback):
    """Consume EMI paid events and trigger notifications."""
    try:
        connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
        channel = await connection.channel()
        queue = await channel.declare_queue("emi.paid", durable=True)

        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    payload = json.loads(message.body.decode())
                    await notification_callback(payload)
    except Exception as e:
        print(f"Event consumer failed: {e}")