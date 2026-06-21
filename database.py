"""
database.py — Supabase connection setup.

This file creates ONE shared Supabase client that every endpoint in main.py
reuses. Credentials are read from environment variables (never hard-coded),
so the same code works locally (.env file) and on Render (dashboard env vars).
"""
import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()  # reads .env file when running locally; no-op on Render (vars already set)

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError(
        "Missing SUPABASE_URL or SUPABASE_KEY environment variables. "
        "Create a .env file locally, or set them in Render's dashboard."
    )


def get_client(access_token: str | None = None) -> Client:
    """
    Returns a Supabase client.

    If access_token is provided (the logged-in user's JWT from the frontend),
    the client acts AS that user — so Row Level Security policies apply
    correctly and each user only ever sees their own rows.

    Without a token, the client only has anonymous (anon) permissions,
    which our RLS policies block from reading/writing any table data.
    """
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    if access_token:
        client.postgrest.auth(access_token)
    return client
