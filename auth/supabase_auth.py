import os
from dotenv import load_dotenv
from supabase import create_client, Client
from core.exceptions import AuthError


load_dotenv()
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(url, key)


def sign_up(email, password):
    try:
        return supabase.auth.sign_up({"email": email, "password": password})
    except Exception as e:
        raise AuthError(f"Sign up failed: {e}") from e


def sign_in(email, password):
    try:
        return supabase.auth.sign_in_with_password({"email": email, "password": password})
    except Exception as e:
        raise AuthError(f"Sign in failed: {e}") from e


def get_user_from_token(access_token):
    """
    Validates an access token against Supabase and returns the associated user.
    This is what proves a request's identity server-side, instead of trusting
    a client-supplied user_id.
    """
    try:
        response = supabase.auth.get_user(access_token)
    except Exception as e:
        raise AuthError(f"Token validation failed: {e}") from e

    if response is None or response.user is None:
        raise AuthError("Invalid or expired token")

    return response.user


def sign_out(access_token, refresh_token):
    """
    Revokes the given session's refresh token server-side, so it can no longer
    be used to mint new access tokens. Uses a fresh client scoped to this one
    session rather than the shared module-level `supabase` client, since
    set_session()/sign_out() mutate client-instance state and the shared
    client is used concurrently across requests for other users.
    """
    try:
        session_client = create_client(url, key)
        session_client.auth.set_session(access_token, refresh_token)
        session_client.auth.sign_out()
    except Exception as e:
        raise AuthError(f"Sign out failed: {e}") from e


def delete_own_account(access_token):
    """
    Calls the delete_own_account() Postgres RPC — a SECURITY DEFINER
    function (created directly in Supabase's SQL editor, not by this app)
    that deletes exactly the caller's own auth.users row, scoped by
    auth.uid() from their token. The anon key alone can't delete auth
    users at all; this RPC is what grants a user permission to delete only
    themselves without handing the backend a full service-role key.

    Uses a fresh client authenticated as the caller (via postgrest.auth(),
    which only needs the access token, unlike sign_out()'s set_session())
    rather than the shared module-level client, for the same concurrency
    reason as sign_out().
    """
    try:
        session_client = create_client(url, key)
        session_client.postgrest.auth(access_token)
        session_client.rpc("delete_own_account").execute()
    except Exception as e:
        raise AuthError(f"Account deletion failed: {e}") from e
