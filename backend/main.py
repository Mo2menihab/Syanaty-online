"""
main.py — SYANATY backend API.

Endpoints mirror the data the frontend used to keep in localStorage:
cars, parts, history, expenses — now backed by Supabase (Postgres + Auth).

Run locally:    uvicorn main:app --reload
Deployed on:    Render.com (see render.yaml / start command)
"""
from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional

from database import get_client
from models import (
    SignUpRequest, LoginRequest,
    CarCreate, CarUpdate,
    PartCreate, PartUpdate,
    HistoryCreate, HistoryUpdate,
    ExpenseCreate,
)

app = FastAPI(title="SYANATY API")

# Allow the frontend (GitHub Pages, or any origin while testing) to call this API.
# Tighten allow_origins to your exact GitHub Pages URL once it's live, for safety.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ══════════════════════════════════════════════════════
#  AUTH HELPER — extracts the user's token from the request
# ══════════════════════════════════════════════════════
def get_token(authorization: Optional[str] = Header(None)) -> str:
    """
    Frontend sends: Authorization: Bearer <access_token>
    This pulls just the token part out, and rejects requests with no token —
    every endpoint below (except signup/login) requires the user to be logged in.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    return authorization.removeprefix("Bearer ").strip()


def get_user_id(token: str = Depends(get_token)) -> tuple[str, str]:
    """Validates the token with Supabase and returns (user_id, token)."""
    client = get_client(token)
    try:
        user = client.auth.get_user(token)
        return user.user.id, token
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired session")


# ══════════════════════════════════════════════════════
#  AUTH ROUTES
# ══════════════════════════════════════════════════════
@app.post("/auth/signup")
def signup(body: SignUpRequest):
    client = get_client()
    try:
        result = client.auth.sign_up({
            "email": body.email,
            "password": body.password,
            "options": {"data": {"name": body.name}},
        })
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not result.user:
        raise HTTPException(status_code=400, detail="Sign up failed")

    # Create a default car for the new user right away, so the Garage tab
    # has something to show on first login (mirrors the old localStorage default).
    if result.session:
        authed_client = get_client(result.session.access_token)
        authed_client.table("cars").insert({
            "user_id": result.user.id,
            "name": f"{body.name}'s Car",
            "year": 2020,
            "emoji": "🚗",
            "odometer": 0,
        }).execute()

    return {
        "user_id": result.user.id,
        "email": result.user.email,
        "access_token": result.session.access_token if result.session else None,
        "refresh_token": result.session.refresh_token if result.session else None,
    }


@app.post("/auth/login")
def login(body: LoginRequest):
    client = get_client()
    try:
        result = client.auth.sign_in_with_password({
            "email": body.email,
            "password": body.password,
        })
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    return {
        "user_id": result.user.id,
        "email": result.user.email,
        "access_token": result.session.access_token,
        "refresh_token": result.session.refresh_token,
    }


@app.post("/auth/refresh")
def refresh(refresh_token: str):
    client = get_client()
    try:
        result = client.auth.refresh_session(refresh_token)
    except Exception:
        raise HTTPException(status_code=401, detail="Could not refresh session")
    return {
        "access_token": result.session.access_token,
        "refresh_token": result.session.refresh_token,
    }


# ══════════════════════════════════════════════════════
#  CARS
# ══════════════════════════════════════════════════════
@app.get("/cars")
def list_cars(auth=Depends(get_user_id)):
    user_id, token = auth
    client = get_client(token)
    res = client.table("cars").select("*").eq("user_id", user_id).execute()
    return res.data


@app.post("/cars")
def create_car(body: CarCreate, auth=Depends(get_user_id)):
    user_id, token = auth
    client = get_client(token)
    res = client.table("cars").insert({**body.model_dump(), "user_id": user_id}).execute()
    return res.data[0]


@app.patch("/cars/{car_id}")
def update_car(car_id: str, body: CarUpdate, auth=Depends(get_user_id)):
    user_id, token = auth
    client = get_client(token)
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    res = client.table("cars").update(updates).eq("id", car_id).eq("user_id", user_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Car not found")
    return res.data[0]


@app.delete("/cars/{car_id}")
def delete_car(car_id: str, auth=Depends(get_user_id)):
    user_id, token = auth
    client = get_client(token)
    client.table("cars").delete().eq("id", car_id).eq("user_id", user_id).execute()
    return {"deleted": True}


# ══════════════════════════════════════════════════════
#  PARTS CATALOG
# ══════════════════════════════════════════════════════
@app.get("/parts")
def list_parts(car_id: str, auth=Depends(get_user_id)):
    user_id, token = auth
    client = get_client(token)
    res = (client.table("parts").select("*")
           .eq("user_id", user_id).eq("car_id", car_id).execute())
    return res.data


@app.post("/parts")
def create_part(body: PartCreate, auth=Depends(get_user_id)):
    user_id, token = auth
    client = get_client(token)
    data = body.model_dump()
    data["last_replaced_date"] = data["last_replaced_date"].isoformat()
    res = client.table("parts").insert({**data, "user_id": user_id}).execute()
    return res.data[0]


@app.patch("/parts/{part_id}")
def update_part(part_id: str, body: PartUpdate, auth=Depends(get_user_id)):
    user_id, token = auth
    client = get_client(token)
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    if "last_replaced_date" in updates:
        updates["last_replaced_date"] = updates["last_replaced_date"].isoformat()
    res = (client.table("parts").update(updates)
           .eq("id", part_id).eq("user_id", user_id).execute())
    if not res.data:
        raise HTTPException(status_code=404, detail="Part not found")
    return res.data[0]


@app.delete("/parts/{part_id}")
def delete_part(part_id: str, auth=Depends(get_user_id)):
    user_id, token = auth
    client = get_client(token)
    client.table("parts").delete().eq("id", part_id).eq("user_id", user_id).execute()
    return {"deleted": True}


# ══════════════════════════════════════════════════════
#  MAINTENANCE HISTORY
# ══════════════════════════════════════════════════════
@app.get("/history")
def list_history(car_id: str, auth=Depends(get_user_id)):
    user_id, token = auth
    client = get_client(token)
    res = (client.table("history").select("*")
           .eq("user_id", user_id).eq("car_id", car_id)
           .order("date", desc=True).execute())
    return res.data


@app.post("/history")
def create_history(body: HistoryCreate, auth=Depends(get_user_id)):
    user_id, token = auth
    client = get_client(token)
    data = body.model_dump()
    data["date"] = data["date"].isoformat()
    res = client.table("history").insert({**data, "user_id": user_id}).execute()
    return res.data[0]


@app.patch("/history/{record_id}")
def update_history(record_id: str, body: HistoryUpdate, auth=Depends(get_user_id)):
    user_id, token = auth
    client = get_client(token)
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    if "date" in updates:
        updates["date"] = updates["date"].isoformat()
    res = (client.table("history").update(updates)
           .eq("id", record_id).eq("user_id", user_id).execute())
    if not res.data:
        raise HTTPException(status_code=404, detail="Record not found")
    return res.data[0]


@app.delete("/history/{record_id}")
def delete_history(record_id: str, auth=Depends(get_user_id)):
    user_id, token = auth
    client = get_client(token)
    client.table("history").delete().eq("id", record_id).eq("user_id", user_id).execute()
    return {"deleted": True}


# ══════════════════════════════════════════════════════
#  EXPENSES
# ══════════════════════════════════════════════════════
@app.get("/expenses")
def list_expenses(car_id: str, month: str, auth=Depends(get_user_id)):
    """month format: YYYY-MM — matches the frontend's month selector."""
    user_id, token = auth
    client = get_client(token)
    res = (client.table("expenses").select("*")
           .eq("user_id", user_id).eq("car_id", car_id)
           .gte("date", f"{month}-01").lt("date", f"{month}-32")
           .order("date", desc=True).execute())
    return res.data


@app.post("/expenses")
def create_expense(body: ExpenseCreate, auth=Depends(get_user_id)):
    user_id, token = auth
    client = get_client(token)
    data = body.model_dump()
    data["date"] = data["date"].isoformat()
    if data["type"] not in ("fuel", "maintenance"):
        raise HTTPException(status_code=400, detail="type must be 'fuel' or 'maintenance'")
    res = client.table("expenses").insert({**data, "user_id": user_id}).execute()
    return res.data[0]


@app.delete("/expenses/{expense_id}")
def delete_expense(expense_id: str, auth=Depends(get_user_id)):
    user_id, token = auth
    client = get_client(token)
    client.table("expenses").delete().eq("id", expense_id).eq("user_id", user_id).execute()
    return {"deleted": True}


# ══════════════════════════════════════════════════════
#  HEALTH CHECK (for Render to confirm the service is alive)
# ══════════════════════════════════════════════════════
@app.get("/")
def health():
    return {"status": "ok", "service": "SYANATY API"}
