"""FastAPI dependency injection."""
from __future__ import annotations
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import create_client, Client
from jose import jwt, JWTError
from config import settings

security = HTTPBearer()

_supabase_client: Client | None = None


def get_supabase() -> Client:
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = create_client(
            settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY
        )
    return _supabase_client


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    supabase: Client = Depends(get_supabase),
) -> dict:
    """Validate Supabase JWT and return user payload."""
    token = credentials.credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Verify JWT using Supabase JWT secret
        payload = jwt.decode(
            token,
            settings.SUPABASE_ANON_KEY,
            algorithms=["HS256"],
            options={"verify_aud": False},
        )
        user_id: str = payload.get("sub")
        if not user_id:
            raise credentials_exception
        return {"id": user_id, "email": payload.get("email", ""), "role": payload.get("role", "authenticated")}
    except JWTError:
        # Fallback: use Supabase admin API to verify token
        try:
            user_resp = supabase.auth.get_user(token)
            if user_resp.user:
                return {
                    "id": user_resp.user.id,
                    "email": user_resp.user.email,
                    "role": "authenticated",
                }
        except Exception:
            pass
        raise credentials_exception


async def require_active_subscription(
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
) -> dict:
    """Require active or trialing subscription."""
    resp = (
        supabase.table("subscriptions")
        .select("status, trial_end")
        .eq("user_id", current_user["id"])
        .single()
        .execute()
    )
    if not resp.data:
        raise HTTPException(status_code=402, detail="No subscription found")

    allowed_statuses = {"trialing", "active"}
    if resp.data["status"] not in allowed_statuses:
        raise HTTPException(status_code=402, detail=f"Subscription {resp.data['status']}")

    return current_user
