class GeminiAPIError(Exception):
    """Raised when a call to the Gemini API fails, so callers can handle it per-request instead of crashing the process."""


class AuthError(Exception):
    """Raised when a Supabase auth operation (sign up, sign in, sign out, token validation) fails."""
