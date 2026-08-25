import os
from dotenv import load_dotenv
from supabase import create_client, Client


load_dotenv()
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(url, key)

def sign_up(email, password):
    try:
        response = supabase.auth.sign_up({"email": email, "password": password})
        return response
    except Exception as e:
        print("Sign up failed:", e)
        return None

def sign_in(email, password):
    try:
        response = supabase.auth.sign_in_with_password({"email": email, "password": password})
        return response
    except Exception as e:
        print("Sign in failed:", e)
        return None

def sign_out():
    try:
        supabase.auth.sign_out()
        return True
    except Exception as e:
        print("Sign out failed:", e)
        return False

