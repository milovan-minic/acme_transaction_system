"""
CSV import tool for the ACME Transactions System.

- Loads transactions from a CSV file and validates each row.
- Inserts valid transactions into the database.
- Flags and logs suspicious (amount > 10000) and duplicate transactions.
- Saves invalid or malformed rows to the rejected_records table for later review.
- Designed for use in Docker Compose with PostgreSQL.

Usage:
    python csv_importer.py data/in/sample_transactions.csv
"""

import csv
import sys
import logging
from datetime import datetime
from sqlalchemy.orm import Session
from db import engine
from models import Transaction, TransactionStatus, RejectedRecord
import argparse

logging.basicConfig(level=logging.INFO)

SUSPICIOUS_AMOUNT = 10000

# Expected CSV columns:
# transaction_id,sender_id,receiver_id,amount,currency,timestamp,status

def validate_row(row):
    """
    Validate a CSV row for required fields, types, and status.

    Args:
        row (dict): The CSV row as a dict.
    Returns:
        (bool, str or None): (True, None) if valid, (False, reason) if invalid.
    """
    required_fields = [
        "transaction_id", "sender_id", "receiver_id", "amount", "currency", "timestamp", "status"
    ]
    for field in required_fields:
        if field not in row or not row[field]:
            return False, f"Missing field: {field}"
    try:
        float(row["amount"])
        datetime.fromisoformat(row["timestamp"].replace("Z", "+00:00"))
        if row["status"] not in [s.value for s in TransactionStatus]:
            return False, f"Invalid status: {row['status']}"
    except Exception as e:
        return False, str(e)
    return True, None

def import_csv(filename):
    """
    Import transactions from a CSV file, validate, insert, flag suspicious, and handle duplicates/invalids.

    Args:
        filename (str): Path to the CSV file.
    """
    with open(filename, newline='') as csvfile, Session(engine) as session:
        reader = csv.DictReader(csvfile)
        for row in reader:
            valid, error = validate_row(row)
            if not valid:
                logging.error(f"Invalid row: {error} | {row}")
                rec = RejectedRecord(reason=error, payload=str(row), source="csv")
                session.add(rec)
                continue
            if session.get(Transaction, row["transaction_id"]):
                logging.warning(f"Duplicate transaction: {row['transaction_id']}")
                continue
            suspicious = float(row["amount"]) > SUSPICIOUS_AMOUNT
            tx = Transaction(
                id=row["transaction_id"],
                sender_id=row["sender_id"],
                receiver_id=row["receiver_id"],
                amount=float(row["amount"]),
                currency=row["currency"],
                timestamp=datetime.fromisoformat(row["timestamp"].replace("Z", "+00:00")),
                status=TransactionStatus(row["status"])
            )
            session.add(tx)
            if suspicious:
                logging.warning(f"Suspicious transaction: {row['transaction_id']} amount={row['amount']}")
        session.commit()
        logging.info("CSV import complete.")

def main():
    parser = argparse.ArgumentParser(description="Import transactions from a CSV file.")
    parser.add_argument("filename", help="Path to the CSV file to import")
    args = parser.parse_args()
    try:
        import_csv(args.filename)
    except FileNotFoundError:
        print(f"Error: File not found: {args.filename}")
        exit(1)
    except Exception as e:
        print(f"Error during import: {e}")
        exit(1)

if __name__ == "__main__":
    main() 