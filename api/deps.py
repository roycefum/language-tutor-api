from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from auth.supabase_auth import get_user_from_token

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
