"""
Reporting logic for the ACME Transactions System.
Provides functions to fetch payments and daily totals for users, with optional date filtering.
"""

from sqlalchemy.orm import Session
from sqlalchemy import func
from db import engine
from models import Transaction
from datetime import date
from typing import Optional, List, Dict

def get_payments_by_user(user_id: str, start_date: Optional[date] = None, end_date: Optional[date] = None, db: Session = None) -> List[Dict]:
    """
    Retrieve all payments sent or received by a user, optionally filtered by date range.

    Args:
        user_id (str): The user ID to query.
        start_date (date, optional): Start date (inclusive).
        end_date (date, optional): End date (exclusive).

    Returns:
        List[Dict]: List of transaction dicts, each with keys:
            - id, sender_id, receiver_id, amount, currency, timestamp, status
    """
    if not db:
        with Session() as session:
            # Query for transactions where the user is sender or receiver
            query = session.query(Transaction).filter(
                (Transaction.sender_id == user_id) | (Transaction.receiver_id == user_id)
            )
            if start_date:
                query = query.filter(Transaction.timestamp >= start_date)
            if end_date:
                query = query.filter(Transaction.timestamp < end_date)
            results = []
            for tx in query.order_by(Transaction.timestamp).all():
                results.append({
                    "id": tx.id,
                    "sender_id": tx.sender_id,
                    "receiver_id": tx.receiver_id,
                    "amount": tx.amount,
                    "currency": tx.currency,
                    "timestamp": tx.timestamp.isoformat(),
                    "status": tx.status.value
                })
            return results
    else:
        # Use db for all queries
        query = db.query(Transaction).filter(
            ((Transaction.sender_id == user_id) | (Transaction.receiver_id == user_id))
        )
        if start_date:
            query = query.filter(Transaction.timestamp >= start_date)
        if end_date:
            query = query.filter(Transaction.timestamp <= end_date)
        results = []
        for tx in query.order_by(Transaction.timestamp).all():
            results.append({
                "id": tx.id,
                "sender_id": tx.sender_id,
                "receiver_id": tx.receiver_id,
                "amount": tx.amount,
                "currency": tx.currency,
                "timestamp": tx.timestamp.isoformat(),
                "status": tx.status.value
            })
        return results

def get_daily_totals(user_id: str, start_date: Optional[date] = None, end_date: Optional[date] = None, db: Session = None) -> List[Dict]:
    """
    Retrieve daily totals of sent and received amounts for a user, optionally filtered by date range.

    Args:
        user_id (str): The user ID to query.
        start_date (date, optional): Start date (inclusive).
        end_date (date, optional): End date (exclusive).

    Returns:
        List[Dict]: List of dicts, each with keys:
            - day (str, ISO date), total_sent (float), total_received (float)
    """
    if not db:
        with Session() as session:
            filters = []
            if start_date:
                filters.append(Transaction.timestamp >= start_date)
            if end_date:
                filters.append(Transaction.timestamp < end_date)
            # Aggregate sent totals per day
            sent = session.query(
                func.date(Transaction.timestamp).label("day"),
                func.sum(Transaction.amount).label("total_sent")
            ).filter(Transaction.sender_id == user_id, *filters).group_by(func.date(Transaction.timestamp)).all()
            # Aggregate received totals per day
            received = session.query(
                func.date(Transaction.timestamp).label("day"),
                func.sum(Transaction.amount).label("total_received")
            ).filter(Transaction.receiver_id == user_id, *filters).group_by(func.date(Transaction.timestamp)).all()
            # Merge sent and received totals by day
            totals = {}
            for row in sent:
                totals.setdefault(row.day, {})["total_sent"] = float(row.total_sent or 0)
            for row in received:
                totals.setdefault(row.day, {})["total_received"] = float(row.total_received or 0)
            # Format output as a sorted list of dicts
            output = []
            for day in sorted(totals.keys()):
                # Handle both string (SQLite) and date (PostgreSQL) day values
                if hasattr(day, "isoformat"):
                    day_str = day.isoformat()
                else:
                    day_str = str(day)
                output.append({
                    "day": day_str,
                    "total_sent": totals[day].get("total_sent", 0.0),
                    "total_received": totals[day].get("total_received", 0.0)
                })
            return output
    else:
        # Use db for all queries
        filters = []
        if start_date:
            filters.append(Transaction.timestamp >= start_date)
        if end_date:
            filters.append(Transaction.timestamp < end_date)
        # Aggregate sent totals per day
        sent = db.query(
            func.date(Transaction.timestamp).label("day"),
            func.sum(Transaction.amount).label("total_sent")
        ).filter(Transaction.sender_id == user_id, *filters).group_by(func.date(Transaction.timestamp)).all()
        # Aggregate received totals per day
        received = db.query(
            func.date(Transaction.timestamp).label("day"),
            func.sum(Transaction.amount).label("total_received")
        ).filter(Transaction.receiver_id == user_id, *filters).group_by(func.date(Transaction.timestamp)).all()
        # Merge sent and received totals by day
        totals = {}
        for row in sent:
            totals.setdefault(row.day, {})["total_sent"] = float(row.total_sent or 0)
        for row in received:
            totals.setdefault(row.day, {})["total_received"] = float(row.total_received or 0)
        # Format output as a sorted list of dicts
        output = []
        for day in sorted(totals.keys()):
            # Handle both string (SQLite) and date (PostgreSQL) day values
            if hasattr(day, "isoformat"):
                day_str = day.isoformat()
            else:
                day_str = str(day)
            output.append({
                "day": day_str,
                "total_sent": totals[day].get("total_sent", 0.0),
                "total_received": totals[day].get("total_received", 0.0)
            })
        return output 