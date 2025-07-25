"""
Unit tests for transaction validation logic in the ACME Transactions System.
Covers validation functions from csv_importer and queue_consumer.
"""

import pytest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from csv_importer import validate_row
from queue_consumer import validate_message
from datetime import datetime

# Sample valid transaction
valid_tx = {
    "transaction_id": "tx100",
    "sender_id": "user1",
    "receiver_id": "user2",
    "amount": "250.00",
    "currency": "USD",
    "timestamp": "2025-05-01T12:00:00Z",
    "status": "completed"
}

def test_validate_row_valid():
    valid, error = validate_row(valid_tx)
    assert valid
    assert error is None

def test_validate_row_missing_field():
    tx = valid_tx.copy()
    del tx["receiver_id"]
    valid, error = validate_row(tx)
    assert not valid
    assert "Missing field" in error

def test_validate_row_invalid_amount():
    tx = valid_tx.copy()
    tx["amount"] = "not_a_number"
    valid, error = validate_row(tx)
    assert not valid
    assert "could not convert" in error or "invalid" in error.lower()

def test_validate_row_invalid_status():
    tx = valid_tx.copy()
    tx["status"] = "not_a_status"
    valid, error = validate_row(tx)
    assert not valid
    assert "Invalid status" in error

def test_validate_row_invalid_timestamp():
    tx = valid_tx.copy()
    tx["timestamp"] = "not_a_timestamp"
    valid, error = validate_row(tx)
    assert not valid
    assert "Invalid isoformat string" in error or "invalid" in error.lower()

def test_validate_message_valid():
    valid, error = validate_message(valid_tx)
    assert valid
    assert error is None

def test_validate_message_missing_field():
    tx = valid_tx.copy()
    del tx["currency"]
    valid, error = validate_message(tx)
    assert not valid
    assert "Missing field" in error

def test_validate_message_invalid_amount():
    tx = valid_tx.copy()
    tx["amount"] = "bad"
    valid, error = validate_message(tx)
    assert not valid
    assert "could not convert" in error or "invalid" in error.lower()

def test_validate_message_invalid_status():
    tx = valid_tx.copy()
    tx["status"] = "bad_status"
    valid, error = validate_message(tx)
    assert not valid
    assert "Invalid status" in error

def test_validate_message_invalid_timestamp():
    tx = valid_tx.copy()
    tx["timestamp"] = "bad_time"
    valid, error = validate_message(tx)
    assert not valid
    assert "Invalid isoformat string" in error or "invalid" in error.lower() 