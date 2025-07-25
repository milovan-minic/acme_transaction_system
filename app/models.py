"""
SQLAlchemy ORM models for the ACME Transactions System.
Defines the database schema for users, currencies, transactions, and rejected records.

Each model includes detailed docstrings for maintainability and clarity.
"""

from sqlalchemy import Column, String, Integer, Float, DateTime, Enum, ForeignKey, Text, Boolean
from sqlalchemy.orm import declarative_base, relationship
import enum
from datetime import datetime

Base = declarative_base()

class TransactionStatus(enum.Enum):
    """
    Enumeration of possible transaction statuses for a payment transaction.
    """
    pending = "pending"
    completed = "completed"
    failed = "failed"

class User(Base):
    """
    Represents a user in the system.

    Attributes:
        id (str): Unique user identifier.
        name (str): User's display name.
        sent_transactions (List[Transaction]): Transactions where this user is the sender.
        received_transactions (List[Transaction]): Transactions where this user is the receiver.
    """
    __tablename__ = "users"
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    sent_transactions = relationship(
        "Transaction",
        back_populates="sender",
        foreign_keys='Transaction.sender_id',
        doc="Transactions sent by this user."
    )
    received_transactions = relationship(
        "Transaction",
        back_populates="receiver",
        foreign_keys='Transaction.receiver_id',
        doc="Transactions received by this user."
    )
    deleted = Column(Boolean, default=False, nullable=False)

    @classmethod
    def active(cls, session):
        return session.query(cls).filter(cls.deleted == False)

class Currency(Base):
    """
    Represents a currency (e.g., USD, EUR).

    Attributes:
        code (str): ISO currency code (3 chars).
        name (str): Currency name.
    """
    __tablename__ = "currency"
    code = Column(String(3), primary_key=True)
    name = Column(String, nullable=False)
    deleted = Column(Boolean, default=False, nullable=False)

    @classmethod
    def active(cls, session):
        return session.query(cls).filter(cls.deleted == False)

class Transaction(Base):
    """
    Represents a payment transaction between two users.

    Attributes:
        id (str): Unique transaction ID.
        sender_id (str): User ID of sender.
        receiver_id (str): User ID of receiver.
        amount (float): Transaction amount.
        currency (str): Currency code.
        timestamp (datetime): When the transaction occurred.
        status (TransactionStatus): Transaction status (pending, completed, failed).
        sender (User): Sender user object.
        receiver (User): Receiver user object.
        currency_rel (Currency): Currency object.
    """
    __tablename__ = "transactions"
    id = Column(String, primary_key=True)
    sender_id = Column(String, ForeignKey("users.id"), nullable=False)
    receiver_id = Column(String, ForeignKey("users.id"), nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String(3), ForeignKey("currency.code"), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    status = Column(Enum(TransactionStatus), nullable=False)
    sender = relationship(
        "User",
        foreign_keys=[sender_id],
        back_populates="sent_transactions",
        doc="Sender user object."
    )
    receiver = relationship(
        "User",
        foreign_keys=[receiver_id],
        back_populates="received_transactions",
        doc="Receiver user object."
    )
    currency_rel = relationship(
        "Currency",
        doc="Currency object for this transaction."
    )

class RejectedRecord(Base):
    """
    Stores any rejected or invalid data from any ingestion source (queue, CSV, etc).

    Attributes:
        id (int): Auto-incremented primary key.
        received_at (datetime): When the record was received.
        reason (str): Why the record was rejected.
        payload (str): Original data (as text).
        source (str): Source of the data (e.g., 'queue', 'csv').
    """
    __tablename__ = "rejected_records"
    id = Column(Integer, primary_key=True, autoincrement=True)
    received_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    reason = Column(String, nullable=False)
    payload = Column(Text, nullable=False)
    source = Column(String, nullable=False, default="unknown") 