"""Integrations Hub API — HubSpot, Gmail, Slack, Zoom."""
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from supabase import Client
from dependencies import get_supabase, require_active_subscription
from models.schemas import IntegrationOut, TriggerSyncRequest
from services.hubspot_service import HubSpotService
from config import settings

router = APIRouter(prefix="/integrations", tags=["integrations"])


def _get_hubspot(supabase: Client) -> HubSpotService:
    return HubSpotService(
        supabase=supabase,
        client_id=settings.HUBSPOT_CLIENT_ID,
        client_secret=settings.HUBSPOT_CLIENT_SECRET,
        redirect_uri=settings.HUBSPOT_REDIRECT_URI,
    )


@router.get("", response_model=list[IntegrationOut])
async def list_integrations(
    current_user: dict = Depends(require_active_subscription),
    supabase: Client = Depends(get_supabase),
):
    resp = (
        supabase.table("integrations")
        .select("*")
        .eq("user_id", current_user["id"])
        .execute()
    )
    return resp.data or []


@router.get("/hubspot/connect")
async def hubspot_connect(
    current_user: dict = Depends(require_active_subscription),
    supabase: Client = Depends(get_supabase),
):
    """Initiate HubSpot OAuth flow."""
    hs = _get_hubspot(supabase)
    auth_url = hs.get_auth_url(current_user["id"])
    return {"auth_url": auth_url}


@router.get("/hubspot/callback")
async def hubspot_callback(
    code: str,
    state: str = None,
    supabase: Client = Depends(get_supabase),
):
    """HubSpot OAuth callback — state = user_id."""
    if not state:
        raise HTTPException(status_code=400, detail="Missing state (user_id)")
    hs = _get_hubspot(supabase)
    result = await hs.exchange_code(code, state)
    return RedirectResponse(url=f"{settings.FRONTEND_URL}/integrations?connected=hubspot")


@router.post("/hubspot/sync")
async def hubspot_sync(
    body: TriggerSyncRequest,
    current_user: dict = Depends(require_active_subscription),
    supabase: Client = Depends(get_supabase),
):
    """Trigger HubSpot data sync."""
    # Check connected
    resp = (
        supabase.table("integrations")
        .select("status")
        .eq("user_id", current_user["id"])
        .eq("provider", "hubspot")
        .single()
        .execute()
    )
    if not resp.data or resp.data.get("status") != "connected":
        raise HTTPException(status_code=400, detail="HubSpot not connected")

    hs = _get_hubspot(supabase)
    results = {}

    if "contacts" in body.entity_types:
        results["contacts"] = await hs.sync_contacts(current_user["id"])
    if "deals" in body.entity_types:
        results["deals"] = await hs.sync_deals(current_user["id"])

    return {"sync_results": results}


@router.delete("/{provider}")
async def disconnect_integration(
    provider: str,
    current_user: dict = Depends(require_active_subscription),
    supabase: Client = Depends(get_supabase),
):
    """Disconnect an integration."""
    supabase.table("integrations").update({
        "status": "disconnected",
        "access_token": None,
        "refresh_token": None,
    }).eq("user_id", current_user["id"]).eq("provider", provider).execute()
    return {"disconnected": provider}


@router.get("/{provider}/status")
async def integration_status(
    provider: str,
    current_user: dict = Depends(require_active_subscription),
    supabase: Client = Depends(get_supabase),
):
    resp = (
        supabase.table("integrations")
        .select("status, last_sync_at, account_name, records_synced")
        .eq("user_id", current_user["id"])
        .eq("provider", provider)
        .single()
        .execute()
    )
    if not resp.data:
        return {"status": "disconnected"}
    return resp.data
