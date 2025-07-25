"""
Unit tests for reporting logic in the ACME Transactions System.
Tests get_payments_by_user and get_daily_totals using an in-memory SQLite database.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, date
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import Base, User, Transaction, TransactionStatus
import reporting
from reporting import get_payments_by_user, get_daily_totals

@pytest.fixture(scope="function")
def session():
    # Set up in-memory SQLite DB and create tables
    engine = create_engine("sqlite:///:memory:")
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
    yield session
    session.close()

# Patch the reporting functions to use our test session
@pytest.fixture(autouse=True)
def patch_reporting(monkeypatch, session):
    monkeypatch.setattr(reporting, "Session", lambda *a, **kw: session)


def test_get_payments_by_user(session):
    # user1 is sender or receiver in all 3 transactions
    results = get_payments_by_user("user1")
    assert len(results) == 3
    # user2 is sender or receiver in all 3 transactions
    results = get_payments_by_user("user2")
    assert len(results) == 3
    # Filter by date
    results = get_payments_by_user("user1", start_date=date(2025, 5, 2))
    assert len(results) == 2
    # Filter by date range
    results = get_payments_by_user("user1", start_date=date(2025, 5, 2), end_date=date(2025, 5, 3))
    assert len(results) == 2


def test_get_daily_totals(session):
    # user1 sent on 2025-05-01 and 2025-05-02, received on 2025-05-02
    results = get_daily_totals("user1")
    # Should have entries for 2025-05-01 and 2025-05-02
    days = {r["day"] for r in results}
    assert "2025-05-01" in days
    assert "2025-05-02" in days
    # Check totals for 2025-05-02
    for r in results:
        if r["day"] == "2025-05-02":
            assert r["total_sent"] == 300.0
            assert r["total_received"] == 200.0 