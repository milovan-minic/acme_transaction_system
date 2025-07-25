"""
API router for reporting endpoints in the ACME Transactions System.
Provides endpoints for user/currency management and reporting.
"""

from fastapi import APIRouter, Query, Response, HTTPException, Depends, Path
from fastapi.responses import JSONResponse, StreamingResponse
from reporting import get_payments_by_user, get_daily_totals
from datetime import datetime
import io
import csv
from pydantic import BaseModel
from models import User, Currency
from db import get_db
from sqlalchemy.orm import Session
from typing import Optional

router = APIRouter()
"""
API router instance for reporting endpoints.
"""

def parse_date(date_str):
    """
    Parse a date string in ISO format (YYYY-MM-DD) to a date object.
    Returns None if date_str is None or empty.
    Raises HTTPException(422) if the date is invalid.
    """
    if date_str:
        try:
            return datetime.fromisoformat(date_str).date()
        except ValueError:
            raise HTTPException(status_code=422, detail=f"Invalid date format: {date_str}")
    return None

def to_csv(data, fieldnames):
    """
    Convert a list of dicts to a CSV file-like object.
    Args:
        data (List[Dict]): List of records to write.
        fieldnames (List[str]): CSV column headers.
    Returns:
        StringIO: File-like object containing CSV data.
    """
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for row in data:
        writer.writerow(row)
    output.seek(0)
    return output

class UserCreate(BaseModel):
    id: str
    name: str

class CurrencyCreate(BaseModel):
    code: str
    name: str

class UserUpdate(BaseModel):
    name: str

class CurrencyUpdate(BaseModel):
    name: str

@router.get("/users")
def list_users(db: Session = Depends(get_db)):
    """List all users (not deleted)."""
    users = db.query(User).filter(User.deleted == False).all()
    return [{"id": u.id, "name": u.name} for u in users]

@router.post("/users", status_code=201)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """Create a new user."""
    if db.get(User, user.id):
        raise HTTPException(status_code=409, detail="User already exists")
    u = User(id=user.id, name=user.name)
    db.add(u)
    db.commit()
    return {"id": u.id, "name": u.name}

@router.patch("/users/{user_id}")
def update_user(user_id: str = Path(...), user: UserUpdate = None, db: Session = Depends(get_db)):
    u = db.get(User, user_id)
    if not u or u.deleted:
        raise HTTPException(status_code=404, detail="User not found or deleted")
    u.name = user.name
    db.commit()
    return {"id": u.id, "name": u.name}

@router.delete("/users/{user_id}", status_code=204)
def delete_user(user_id: str = Path(...), db: Session = Depends(get_db)):
    u = db.get(User, user_id)
    if not u or u.deleted:
        raise HTTPException(status_code=404, detail="User not found or already deleted")
    u.deleted = True
    db.commit()
    return Response(status_code=204)

@router.get("/currencies")
def list_currencies(db: Session = Depends(get_db)):
    """List all currencies (not deleted)."""
    currencies = db.query(Currency).filter(Currency.deleted == False).all()
    return [{"code": c.code, "name": c.name} for c in currencies]

@router.post("/currencies", status_code=201)
def create_currency(currency: CurrencyCreate, db: Session = Depends(get_db)):
    """Create a new currency."""
    if db.get(Currency, currency.code):
        raise HTTPException(status_code=409, detail="Currency already exists")
    c = Currency(code=currency.code, name=currency.name)
    db.add(c)
    db.commit()
    return {"code": c.code, "name": c.name}

@router.patch("/currencies/{code}")
def update_currency(code: str = Path(...), currency: CurrencyUpdate = None, db: Session = Depends(get_db)):
    c = db.get(Currency, code)
    if not c or c.deleted:
        raise HTTPException(status_code=404, detail="Currency not found or deleted")
    c.name = currency.name
    db.commit()
    return {"code": c.code, "name": c.name}

@router.delete("/currencies/{code}", status_code=204)
def delete_currency(code: str = Path(...), db: Session = Depends(get_db)):
    c = db.get(Currency, code)
    if not c or c.deleted:
        raise HTTPException(status_code=404, detail="Currency not found or already deleted")
    c.deleted = True
    db.commit()
    return Response(status_code=204)

@router.get("/reports/payments/{user_id}")
def payments_by_user(user_id: str, start_date: Optional[str] = Query(None), end_date: Optional[str] = Query(None), format: str = Query("json"), db: Session = Depends(get_db)):
    """
    Get all payments sent or received by a user, optionally filtered by date range.

    Query Parameters:
        start_date (str, optional): Start date (YYYY-MM-DD)
        end_date (str, optional): End date (YYYY-MM-DD)
        format (str): 'json' or 'csv'

    Returns:
        JSON or CSV response with payment records.
    """
    s_date = parse_date(start_date) if start_date else None
    e_date = parse_date(end_date) if end_date else None
    data = get_payments_by_user(user_id, s_date, e_date, db)
    if format == "csv":
        fieldnames = ["id", "sender_id", "receiver_id", "amount", "currency", "timestamp", "status"]
        csv_file = to_csv(data, fieldnames)
        return StreamingResponse(csv_file, media_type="text/csv", headers={"Content-Disposition": f"attachment; filename=payments_{user_id}.csv"})
    return JSONResponse(content=data)

@router.get("/reports/daily_totals/{user_id}")
def daily_totals(user_id: str, start_date: Optional[str] = Query(None), end_date: Optional[str] = Query(None), format: str = Query("json"), db: Session = Depends(get_db)):
    """
    Get daily totals of sent and received amounts for a user, optionally filtered by date range.

    Query Parameters:
        start_date (str, optional): Start date (YYYY-MM-DD)
        end_date (str, optional): End date (YYYY-MM-DD)
        format (str): 'json' or 'csv'

    Returns:
        JSON or CSV response with daily totals.
    """
    s_date = parse_date(start_date) if start_date else None
    e_date = parse_date(end_date) if end_date else None
    data = get_daily_totals(user_id, s_date, e_date, db)
    if format == "csv":
        fieldnames = ["day", "total_sent", "total_received"]
        csv_file = to_csv(data, fieldnames)
        return StreamingResponse(csv_file, media_type="text/csv", headers={"Content-Disposition": f"attachment; filename=daily_totals_{user_id}.csv"})
    return JSONResponse(content=data) 