"""
CLI management tool for users and currencies in the ACME Transactions System.

Usage examples:
  python manage_cli.py list-users
  python manage_cli.py add-user --id user4 --name "Diana"
  python manage_cli.py edit-user --id user4 --name "Diana Updated"
  python manage_cli.py delete-user --id user4
  python manage_cli.py list-currencies
  python manage_cli.py add-currency --code JPY --name "Japanese Yen"
  python manage_cli.py edit-currency --code JPY --name "Japanese Yen Updated"
  python manage_cli.py delete-currency --code JPY
"""

import argparse
from db import get_session_local
from models import User, Currency

parser = argparse.ArgumentParser(description="Manage users and currencies.")
subparsers = parser.add_subparsers(dest="command")

# List users
subparsers.add_parser("list-users", help="List all users")

# Add user
add_user_parser = subparsers.add_parser("add-user", help="Add a new user")
add_user_parser.add_argument("--id", required=True, help="User ID")
add_user_parser.add_argument("--name", required=True, help="User name")

# List currencies
subparsers.add_parser("list-currencies", help="List all currencies")

# Add currency
add_currency_parser = subparsers.add_parser("add-currency", help="Add a new currency")
add_currency_parser.add_argument("--code", required=True, help="Currency code (3 letters)")
add_currency_parser.add_argument("--name", required=True, help="Currency name")

# Edit user
edit_user_parser = subparsers.add_parser("edit-user", help="Edit a user's name")
edit_user_parser.add_argument("--id", required=True)
edit_user_parser.add_argument("--name", required=True)

# Delete user
del_user_parser = subparsers.add_parser("delete-user", help="Soft delete a user")
del_user_parser.add_argument("--id", required=True)

# Edit currency
edit_cur_parser = subparsers.add_parser("edit-currency", help="Edit a currency's name")
edit_cur_parser.add_argument("--code", required=True)
edit_cur_parser.add_argument("--name", required=True)

# Delete currency
del_cur_parser = subparsers.add_parser("delete-currency", help="Soft delete a currency")
del_cur_parser.add_argument("--code", required=True)


def list_users():
    SessionLocal = get_session_local()
    try:
        with SessionLocal() as session:
            users = User.active(session).all()
            for u in users:
                print(f"{u.id}: {u.name}", flush=True)
    except Exception as e:
        print(f"Error: {e}", flush=True)
        raise

def add_user(user_id, name):
    SessionLocal = get_session_local()
    try:
        with SessionLocal() as session:
            if session.get(User, user_id):
                print(f"User {user_id} already exists.", flush=True)
                return
            u = User(id=user_id, name=name)
            session.add(u)
            session.commit()
            print(f"Added user {user_id}: {name}", flush=True)
    except Exception as e:
        print(f"Error: {e}", flush=True)
        raise

def list_currencies():
    SessionLocal = get_session_local()
    try:
        with SessionLocal() as session:
            currencies = Currency.active(session).all()
            for c in currencies:
                print(f"{c.code}: {c.name}", flush=True)
    except Exception as e:
        print(f"Error: {e}", flush=True)
        raise

def add_currency(code, name):
    SessionLocal = get_session_local()
    try:
        with SessionLocal() as session:
            if session.get(Currency, code):
                print(f"Currency {code} already exists.", flush=True)
                return
            c = Currency(code=code, name=name)
            session.add(c)
            session.commit()
            print(f"Added currency {code}: {name}", flush=True)
    except Exception as e:
        print(f"Error: {e}", flush=True)
        raise

def edit_user(user_id, name):
    SessionLocal = get_session_local()
    try:
        with SessionLocal() as session:
            user = session.get(User, user_id)
            if not user or user.deleted:
                print(f"User {user_id} not found or deleted.", flush=True)
                return
            user.name = name
            session.commit()
            print(f"Updated user {user_id} name to {name}", flush=True)
    except Exception as e:
        print(f"Error: {e}", flush=True)
        raise

def delete_user(user_id):
    SessionLocal = get_session_local()
    try:
        with SessionLocal() as session:
            user = session.get(User, user_id)
            if not user or user.deleted:
                print(f"User {user_id} not found or already deleted.", flush=True)
                return
            user.deleted = True
            session.commit()
            print(f"Soft-deleted user {user_id}", flush=True)
    except Exception as e:
        print(f"Error: {e}", flush=True)
        raise

def edit_currency(code, name):
    SessionLocal = get_session_local()
    try:
        with SessionLocal() as session:
            currency = session.get(Currency, code)
            if not currency or currency.deleted:
                print(f"Currency {code} not found or deleted.", flush=True)
                return
            currency.name = name
            session.commit()
            print(f"Updated currency {code} name to {name}", flush=True)
    except Exception as e:
        print(f"Error: {e}", flush=True)
        raise

def delete_currency(code):
    SessionLocal = get_session_local()
    try:
        with SessionLocal() as session:
            currency = session.get(Currency, code)
            if not currency or currency.deleted:
                print(f"Currency {code} not found or already deleted.", flush=True)
                return
            currency.deleted = True
            session.commit()
            print(f"Soft-deleted currency {code}", flush=True)
    except Exception as e:
        print(f"Error: {e}", flush=True)
        raise


def main():
    args = parser.parse_args()
    if args.command == "list-users":
        list_users()
    elif args.command == "add-user":
        add_user(args.id, args.name)
    elif args.command == "list-currencies":
        list_currencies()
    elif args.command == "add-currency":
        add_currency(args.code, args.name)
    elif args.command == "edit-user":
        edit_user(args.id, args.name)
    elif args.command == "delete-user":
        delete_user(args.id)
    elif args.command == "edit-currency":
        edit_currency(args.code, args.name)
    elif args.command == "delete-currency":
        delete_currency(args.code)
    else:
        parser.print_help()

if __name__ == "__main__":
    main() 