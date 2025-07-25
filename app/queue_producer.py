"""
RabbitMQ producer for the ACME Transactions System.
Sends sample transaction messages to the 'transactions' queue for testing the consumer and validation logic.
"""

import os
import json
import pika
from datetime import datetime

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
QUEUE_NAME = "transactions"

# Sample transactions for testing (includes one invalid message)
sample_transactions = [
    {
        "transaction_id": "tx1001",
        "sender_id": "user1",
        "receiver_id": "user2",
        "amount": 250.00,
        "currency": "USD",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "status": "completed"
    },
    {
        "transaction_id": "tx1002",
        "sender_id": "user2",
        "receiver_id": "user3",
        "amount": 500.00,
        "currency": "EUR",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "status": "pending"
    },
    {
        # Invalid: missing receiver_id
        "transaction_id": "tx1003",
        "sender_id": "user1",
        "amount": 100.00,
        "currency": "GBP",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "status": "failed"
    }
]

def main():
    """
    Sends sample transaction messages to the RabbitMQ 'transactions' queue.
    Used for testing the queue consumer and validation logic.
    """
    params = pika.URLParameters(RABBITMQ_URL)
    connection = pika.BlockingConnection(params)
    channel = connection.channel()
    channel.queue_declare(queue=QUEUE_NAME, durable=True)
    for tx in sample_transactions:
        body = json.dumps(tx)
        channel.basic_publish(
            exchange="",
            routing_key=QUEUE_NAME,
            body=body,
            properties=pika.BasicProperties(delivery_mode=2)  # make message persistent
        )
        print(f"Sent: {body}")
    connection.close()

if __name__ == "__main__":
    main() 