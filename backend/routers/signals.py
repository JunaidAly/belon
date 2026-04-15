"""Signal Intelligence Feed API."""
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Query
from supabase import Client
from dependencies import get_supabase, require_active_subscription
from models.schemas import SignalOut, SignalAction
from services.signal_engine import SIGNAL_DEFINITIONS

router = APIRouter(prefix="/signals", tags=["signals"])


@router.get("", response_model=list[SignalOut])
async def list_signals(
    status: str = Query(default="pending"),
    category: str = Query(default=None),
    severity: str = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    current_user: dict = Depends(require_active_subscription),
    supabase: Client = Depends(get_supabase),
):
    query = (
        supabase.table("signals")
        .select("*")
        .eq("user_id", current_user["id"])
        .order("created_at", desc=True)
        .range(offset, offset + limit - 1)
    )
    if status:
        query = query.eq("status", status)
    if category:
        query = query.eq("category", category)
    if severity:
        query = query.eq("severity", severity)

    resp = query.execute()
    return resp.data or []


@router.get("/stats")
async def signal_stats(
    current_user: dict = Depends(require_active_subscription),
    supabase: Client = Depends(get_supabase),
):
    """Return signal counts by severity and category."""
    resp = (
        supabase.table("signals")
        .select("severity, category, status")
        .eq("user_id", current_user["id"])
        .eq("status", "pending")
        .execute()
    )
    signals = resp.data or []
    by_severity = {}
    by_category = {}
    for s in signals:
        sev = s.get("severity", "medium")
        cat = s.get("category", "deal_health")
        by_severity[sev] = by_severity.get(sev, 0) + 1
        by_category[cat] = by_category.get(cat, 0) + 1

    return {
        "total_pending": len(signals),
        "by_severity": by_severity,
        "by_category": by_category,
    }


@router.post("/{signal_id}/action")
async def action_signal(
    signal_id: str,
    body: SignalAction,
    current_user: dict = Depends(require_active_subscription),
    supabase: Client = Depends(get_supabase),
):
    """Action, dismiss, or snooze a signal."""
    from datetime import datetime
    update = {"status": body.action, "updated_at": datetime.utcnow().isoformat()}
    if body.action == "actioned":
        update["actioned_at"] = datetime.utcnow().isoformat()
    if body.action == "snoozed" and body.snoozed_until:
        update["snoozed_until"] = body.snoozed_until.isoformat()

    resp = (
        supabase.table("signals")
        .update(update)
        .eq("id", signal_id)
        .eq("user_id", current_user["id"])
        .execute()
    )
    if not resp.data:
        raise HTTPException(status_code=404, detail="Signal not found")
    return resp.data[0]


@router.post("/run-engine")
async def trigger_signal_engine(
    current_user: dict = Depends(require_active_subscription),
    supabase: Client = Depends(get_supabase),
):
    """Manually trigger signal engine for current user."""
    from services.signal_engine import SignalEngine
    engine = SignalEngine(supabase)
    count = await engine.run_for_user(current_user["id"])
    return {"signals_generated": count}


@router.get("/catalog")
async def signal_catalog():
    """Return full 100+ signal type catalog (public)."""
    return {
        "count": len(SIGNAL_DEFINITIONS),
        "signals": SIGNAL_DEFINITIONS,
    }
