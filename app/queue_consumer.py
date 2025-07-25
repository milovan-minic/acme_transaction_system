"""
RabbitMQ consumer for the ACME Transactions System.
Listens for transaction messages on the 'transactions' queue, validates, and inserts them into the database. Invalid messages are saved to rejected_records.
"""

import os
import json
import logging
import pika
from sqlalchemy.orm import Session
from db import engine
from models import Transaction, TransactionStatus, RejectedRecord
from datetime import datetime

logging.basicConfig(level=logging.INFO)

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
QUEUE_NAME = "transactions"

# Example of expected JSON message:
# {
#   "transaction_id": "tx123",
#   "sender_id": "user1",
#   "receiver_id": "user2",
#   "amount": 250.00,
#   "currency": "USD",
#   "timestamp": "2025-05-01T12:00:00Z",
#   "status": "completed"
# }

def validate_message(data):
    """
    Validate the structure and content of a transaction message.

    Args:
        data (dict): The transaction message as a dict.
    Returns:
        (bool, str or None): (True, None) if valid, (False, reason) if invalid.
    """
    required_fields = [
        "transaction_id", "sender_id", "receiver_id", "amount", "currency", "timestamp", "status"
    ]
    for field in required_fields:
        if field not in data:
            return False, f"Missing field: {field}"
    try:
        float(data["amount"])
        datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))
        if data["status"] not in [s.value for s in TransactionStatus]:
            return False, f"Invalid status: {data['status']}"
    except Exception as e:
        return False, str(e)
    return True, None

def insert_transaction(data):
    """
    Insert a valid transaction into the database, skipping duplicates.

    Args:
        data (dict): The validated transaction message.
    """
    with Session(engine) as session:
        if session.get(Transaction, data["transaction_id"]):
            logging.warning(f"Duplicate transaction: {data['transaction_id']}")
            return
        tx = Transaction(
            id=data["transaction_id"],
            sender_id=data["sender_id"],
            receiver_id=data["receiver_id"],
            amount=float(data["amount"]),
            currency=data["currency"],
            timestamp=datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00")),
            status=TransactionStatus(data["status"])
        )
        session.add(tx)
        session.commit()
        logging.info(f"Inserted transaction: {tx.id}")

def save_rejected_record(reason, payload, source="queue"):
    """
    Save a rejected or malformed message to the database for later review.

    Args:
        reason (str): Reason for rejection.
        payload (str): Original message payload.
        source (str): Source of the message (default: 'queue').
    """
    with Session(engine) as session:
        rec = RejectedRecord(reason=reason, payload=payload, source=source)
        session.add(rec)
        session.commit()
        logging.info(f"Saved rejected record: {reason}")

def callback(ch, method, properties, body):
    """
    Callback for RabbitMQ message consumption. Validates and processes each message.

    Args:
        ch, method, properties: RabbitMQ delivery parameters.
        body (bytes): The message body.
    """
    try:
        data = json.loads(body)
        valid, error = validate_message(data)
        if not valid:
            logging.error(f"Invalid message: {error} | {body}")
            save_rejected_record(error, body.decode() if isinstance(body, bytes) else str(body), source="queue")
            return
        insert_transaction(data)
    except Exception as e:
        logging.error(f"Malformed message: {e} | {body}")
        save_rejected_record(str(e), body.decode() if isinstance(body, bytes) else str(body), source="queue")

def main():
    """
    Main entrypoint: Connects to RabbitMQ and starts consuming messages.
    """
    params = pika.URLParameters(RABBITMQ_URL)
    connection = pika.BlockingConnection(params)
    channel = connection.channel()
    channel.queue_declare(queue=QUEUE_NAME, durable=True)
    logging.info(f"Listening for messages on queue '{QUEUE_NAME}'...")
    channel.basic_consume(queue=QUEUE_NAME, on_message_callback=callback, auto_ack=True)
    channel.start_consuming()

if __name__ == "__main__":
    main() 