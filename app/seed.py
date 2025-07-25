"""
Database seeding script for the ACME Transactions System.
Populates the database with sample users and currencies for testing and development.
"""

import os
from sqlalchemy.orm import Session
from db import engine
from models import User, Currency

# Sample data for initial seeding
users = [
    User(id="user1", name="Alice"),
    User(id="user2", name="Bob"),
    User(id="user3", name="Charlie"),
]
currencies = [
    Currency(code="USD", name="US Dollar"),
    Currency(code="EUR", name="Euro"),
    Currency(code="GBP", name="British Pound"),
]

def seed():
    """
    Insert sample users and currencies into the database if they do not already exist.

    This function is idempotent: running it multiple times will not create duplicates.
    """
    with Session(engine) as session:
        # Add users if not present
        for user in users:
            if not session.get(User, user.id):
                session.add(user)
        # Add currencies if not present
        for currency in currencies:
            if not session.get(Currency, currency.code):
                session.add(currency)
        session.commit()
        print("Seeded users and currencies.")

if __name__ == "__main__":
    seed() 