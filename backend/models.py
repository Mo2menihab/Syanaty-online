"""
models.py — Request/response data shapes (Pydantic models).

These mirror exactly what the SYANATY frontend already uses in localStorage:
car, parts, history, expenses. FastAPI uses these to validate incoming
JSON automatically and reject bad requests before they ever reach the database.
"""
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import date


# ── AUTH ──────────────────────────────────────────────
class SignUpRequest(BaseModel):
    email: EmailStr
    password: str
    name: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


# ── CAR ───────────────────────────────────────────────
class CarCreate(BaseModel):
    name: str = "My Car"
    year: int = 2020
    emoji: str = "🚗"
    odometer: int = 0


class CarUpdate(BaseModel):
    name: Optional[str] = None
    year: Optional[int] = None
    emoji: Optional[str] = None
    odometer: Optional[int] = None


# ── PARTS ─────────────────────────────────────────────
class PartCreate(BaseModel):
    car_id: str
    name: str
    interval_km: int
    interval_months: int
    last_replaced_km: int = 0
    last_replaced_date: date
    cost_new: float = 0


class PartUpdate(BaseModel):
    name: Optional[str] = None
    interval_km: Optional[int] = None
    interval_months: Optional[int] = None
    last_replaced_km: Optional[int] = None
    last_replaced_date: Optional[date] = None
    cost_new: Optional[float] = None


# ── HISTORY ───────────────────────────────────────────
class HistoryCreate(BaseModel):
    car_id: str
    date: date
    mileage: int
    service: str
    cost: float = 0
    urgent: bool = False


class HistoryUpdate(BaseModel):
    date: Optional[date] = None
    mileage: Optional[int] = None
    service: Optional[str] = None
    cost: Optional[float] = None
    urgent: Optional[bool] = None


# ── EXPENSES ──────────────────────────────────────────
class ExpenseCreate(BaseModel):
    car_id: str
    type: str  # "fuel" or "maintenance"
    amount: float
    note: Optional[str] = None
    date: date
