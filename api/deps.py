import os

from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from auth.supabase_auth import get_user_from_token
from data.db import get_authed_client

bearer_scheme = HTTPBearer()


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    """
    FastAPI dependency: validates the bearer token against Supabase and
    returns the full user object. FastAPI caches a dependency's result per
    request, so get_current_user_id/require_admin below (which both build
    on this) don't each trigger their own validation round trip.
    """
    return get_user_from_token(credentials.credentials)


def get_current_user_id(user=Depends(get_current_user)) -> str:
    """
    FastAPI dependency: returns the real user id for the calling user.
    Add this as a parameter to any route that needs to know who's calling —
    FastAPI runs it before the route body, and it raises on a missing or
    invalid token, so a route using it can assume the id it receives is real.
    """
    return user.id


def is_admin_user(user) -> bool:
    """
    Admin status comes from the ADMIN_EMAILS environment variable (comma-
    separated), set once on the server — deliberately NOT a column or
    profile field, because anything stored where a user's own requests can
    write to it could be flipped by that user. Server environment can't be.
    """
    allowed = {e.strip().lower() for e in os.getenv("ADMIN_EMAILS", "").split(",") if e.strip()}
    return bool(user.email) and user.email.lower() in allowed


def require_admin(user=Depends(get_current_user)) -> str:
    """
    FastAPI dependency for admin-only routes: returns the admin's user id,
    or raises 404 (not 403) for everyone else so the routes don't even
    reveal that they exist.
    """
    if not is_admin_user(user):
        raise HTTPException(status_code=404, detail="Not found")
    return user.id


def get_db_client(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    """
    FastAPI dependency: builds a Supabase client authenticated as the
    calling user (via data.db.get_authed_client), for routes to pass into
    data/db.py functions. FastAPI caches a dependency's result per request,
    so this builds exactly one client per incoming request, not one per
    database call. Required for Postgres Row Level Security policies
    (keyed off auth.uid()) to recognize who's making each query — a query
    made with the shared anon-key client would have no user identity RLS
    could check.
    """
    return get_authed_client(credentials.credentials)
