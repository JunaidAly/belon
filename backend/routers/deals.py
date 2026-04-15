"""Deals API — pipeline intelligence."""
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Query
from supabase import Client
from dependencies import get_supabase, require_active_subscription
from models.schemas import DealOut, ControlCenterStats

router = APIRouter(prefix="/deals", tags=["deals"])


@router.get("", response_model=list[DealOut])
async def list_deals(
    stage: str = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    current_user: dict = Depends(require_active_subscription),
    supabase: Client = Depends(get_supabase),
):
    query = (
        supabase.table("deals")
        .select("*")
        .eq("user_id", current_user["id"])
        .order("value", desc=True)
        .limit(limit)
    )
    if stage:
        query = query.eq("stage", stage)
    resp = query.execute()
    return resp.data or []


@router.get("/stats", response_model=ControlCenterStats)
async def control_center_stats(
    current_user: dict = Depends(require_active_subscription),
    supabase: Client = Depends(get_supabase),
):
    """Aggregate stats for Automation Control Center."""
    uid = current_user["id"]

    deals_resp = supabase.table("deals").select("value, health_score, stage").eq("user_id", uid).execute()
    deals = deals_resp.data or []

    signals_resp = (
        supabase.table("signals")
        .select("id, status")
        .eq("user_id", uid)
        .execute()
    )
    signals = signals_resp.data or []

    workflows_resp = (
        supabase.table("workflows")
        .select("id, status")
        .eq("user_id", uid)
        .eq("status", "active")
        .execute()
    )

    today_signals = [s for s in signals if s.get("status") == "pending"]
    actioned_today = [s for s in signals if s.get("status") == "actioned"]

    active_deals = [d for d in deals if d.get("stage") not in ("closed_won", "closed_lost")]
    at_risk = [d for d in active_deals if d.get("health_score", 100) < 40]
    at_risk_revenue = sum(d.get("value", 0) for d in at_risk)

    avg_health = (
        int(sum(d.get("health_score", 50) for d in active_deals) / len(active_deals))
        if active_deals else 0
    )

    return ControlCenterStats(
        pipeline_health=avg_health,
        active_deals=len(active_deals),
        at_risk_revenue=at_risk_revenue,
        signals_today=len(today_signals),
        workflows_running=len(workflows_resp.data or []),
        actions_completed_today=len(actioned_today),
        actions_total_today=len(today_signals) + len(actioned_today),
    )
