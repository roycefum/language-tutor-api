from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from auth.supabase_auth import get_user_from_token
from data.db import get_authed_client

bearer_scheme = HTTPBearer()


def get_current_user_id(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> str:
    """
    FastAPI dependency: extracts the bearer token from the Authorization
    header, validates it against Supabase, and returns the real user id.
    Add this as a parameter to any route that needs to know who's calling —
    FastAPI runs it before the route body, and it raises on a missing or
    invalid token, so a route using it can assume the id it receives is real.
    """
    user = get_user_from_token(credentials.credentials)
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
