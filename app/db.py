"""
Database connection and session management for the ACME Transactions System.
Loads environment variables from .env for configuration.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

# Load environment variables from .env file for local development and Docker Compose
load_dotenv()

# Database URL, e.g., postgresql+psycopg2://user:pass@host:port/dbname
DATABASE_URL = os.getenv("DATABASE_URL")

# SQLAlchemy engine for database connections
engine = create_engine(DATABASE_URL)

# Session factory for database operations
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for declarative models (not used directly, but kept for legacy and Alembic compatibility)
Base = declarative_base()

def get_engine():
    return create_engine(os.getenv("DATABASE_URL"))

def get_session_local():
    return sessionmaker(autocommit=False, autoflush=False, bind=get_engine())

SessionLocal = get_session_local()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 