"""AI action endpoints."""
from __future__ import annotations
from fastapi import APIRouter, Depends
from supabase import Client
from dependencies import get_supabase, require_active_subscription
from models.schemas import AIRequest, AIResponse
from services.ai_service import ai_service
import time

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/action", response_model=AIResponse)
async def run_ai_action(
    body: AIRequest,
    current_user: dict = Depends(require_active_subscription),
    supabase: Client = Depends(get_supabase),
):
    """Run an AI action (email draft, lead score, deal analysis, etc.)."""
    result = await ai_service.run_action(
        action_type=body.action_type,
        context=body.context,
        model=body.model,
    )

    # Log to ai_actions table
    log_data = {
        "user_id": current_user["id"],
        "action_type": body.action_type,
        "input_context": body.context,
        "model_used": result["model_used"],
        "output": result["output"][:4000],  # truncate for DB
        "tokens_used": result.get("tokens_used"),
        "latency_ms": result.get("latency_ms"),
        "status": "completed",
    }
    if body.signal_id:
        log_data["signal_id"] = body.signal_id

    try:
        ai_log = supabase.table("ai_actions").insert(log_data).execute()
        if ai_log.data:
            result["action_id"] = ai_log.data[0]["id"]
    except Exception:
        pass  # Logging failure shouldn't break the response

    return result


@router.get("/actions")
async def list_ai_actions(
    limit: int = 20,
    current_user: dict = Depends(require_active_subscription),
    supabase: Client = Depends(get_supabase),
):
    resp = (
        supabase.table("ai_actions")
        .select("id, action_type, model_used, tokens_used, latency_ms, status, created_at")
        .eq("user_id", current_user["id"])
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return resp.data or []
