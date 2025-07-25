"""
API endpoint tests for the ACME Transactions System.
Uses FastAPI's TestClient and a file-based SQLite database for reliable table persistence.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from models import Base, User, Transaction, TransactionStatus
import main
import api
import tempfile
from db import get_db

TEST_DB_PATH = "./test.db"

@pytest.fixture(scope="function")
def client():
    # Create a unique temp file for each test
    with tempfile.NamedTemporaryFile(suffix=".db") as tmp:
        engine = create_engine(f"sqlite:///{tmp.name}")
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()
        # Seed users and transactions
        user1 = User(id="user1", name="Alice")
        user2 = User(id="user2", name="Bob")
        session.add_all([user1, user2])
        txs = [
            Transaction(
                id="tx1",
                sender_id="user1",
                receiver_id="user2",
                amount=100.0,
                currency="USD",
                timestamp=datetime(2025, 5, 1, 12, 0, 0),
                status=TransactionStatus.completed,
            ),
            Transaction(
                id="tx2",
                sender_id="user2",
                receiver_id="user1",
                amount=200.0,
                currency="USD",
                timestamp=datetime(2025, 5, 2, 13, 0, 0),
                status=TransactionStatus.pending,
            ),
            Transaction(
                id="tx3",
                sender_id="user1",
                receiver_id="user2",
                amount=300.0,
                currency="USD",
                timestamp=datetime(2025, 5, 2, 14, 0, 0),
                status=TransactionStatus.failed,
            ),
        ]
        session.add_all(txs)
        session.commit()

        # Patch db and reporting to use the test engine/session
        import db
        import reporting
        db.engine = engine
        db.SessionLocal = Session
        reporting.Session = Session

        # Override get_db dependency
        def override_get_db():
            try:
                yield session
            finally:
                pass
        main.app.dependency_overrides[get_db] = override_get_db

        client = TestClient(main.app)
        yield client
        session.close()
        main.app.dependency_overrides.clear()


def test_payments_by_user_json(client):
    response = client.get("/reports/payments/user1")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 3
    assert any(tx["id"] == "tx1" for tx in data)


def test_payments_by_user_csv(client):
    response = client.get("/reports/payments/user1?format=csv")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    content = response.text
    assert "transaction_id" not in content  # header is 'id' not 'transaction_id'
    assert "tx1" in content


def test_daily_totals_json(client):
    response = client.get("/reports/daily_totals/user1")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert any("day" in row for row in data)


def test_daily_totals_csv(client):
    response = client.get("/reports/daily_totals/user1?format=csv")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    content = response.text
    assert "day" in content
    assert "2025-05-01" in content or "2025-05-02" in content 

def test_payments_by_nonexistent_user(client):
    response = client.get("/reports/payments/nonexistent")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0

def test_daily_totals_nonexistent_user(client):
    response = client.get("/reports/daily_totals/nonexistent")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0

def test_payments_by_user_invalid_format(client):
    response = client.get("/reports/payments/user1?format=xml")
    # Should fallback to JSON or return 422/400
    assert response.status_code in (200, 422, 400)

def test_payments_by_user_malformed_dates(client):
    response = client.get("/reports/payments/user1?start_date=notadate")
    assert response.status_code in (422, 400)
    # Should not crash the server

def test_daily_totals_malformed_dates(client):
    response = client.get("/reports/daily_totals/user1?end_date=notadate")
    assert response.status_code in (422, 400)
    # Should not crash the server 

def test_list_users(client):
    response = client.get("/users")
    assert response.status_code == 200
    data = response.json()
    assert any(u["id"] == "user1" for u in data)
    assert any(u["id"] == "user2" for u in data)

def test_create_user_success(client):
    response = client.post("/users", json={"id": "user3", "name": "Charlie"})
    assert response.status_code == 201
    data = response.json()
    assert data["id"] == "user3"
    # Should now be in the list
    response = client.get("/users")
    assert any(u["id"] == "user3" for u in response.json())

def test_create_user_duplicate(client):
    response = client.post("/users", json={"id": "user1", "name": "Alice"})
    assert response.status_code == 409

def test_list_currencies(client):
    # Add a currency first
    client.post("/currencies", json={"code": "USD", "name": "US Dollar"})
    response = client.get("/currencies")
    assert response.status_code == 200
    data = response.json()
    assert any(c["code"] == "USD" for c in data)

def test_create_currency_success(client):
    response = client.post("/currencies", json={"code": "EUR", "name": "Euro"})
    assert response.status_code == 201
    data = response.json()
    assert data["code"] == "EUR"
    # Should now be in the list
    response = client.get("/currencies")
    assert any(c["code"] == "EUR" for c in response.json())

def test_create_currency_duplicate(client):
    client.post("/currencies", json={"code": "GBP", "name": "British Pound"})
    response = client.post("/currencies", json={"code": "GBP", "name": "British Pound"})
    assert response.status_code == 409 