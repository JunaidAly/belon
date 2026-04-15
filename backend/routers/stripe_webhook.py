"""Stripe webhook handler."""
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Request
from supabase import Client
from dependencies import get_supabase
from services.stripe_service import StripeService
from models.schemas import CreateCheckoutSession
from dependencies import require_active_subscription

router = APIRouter(prefix="/billing", tags=["billing"])


@router.post("/checkout")
async def create_checkout(
    body: CreateCheckoutSession,
    current_user: dict = Depends(require_active_subscription),
    supabase: Client = Depends(get_supabase),
):
    service = StripeService(supabase)
    # Get user profile for name
    profile = supabase.table("profiles").select("full_name").eq("id", current_user["id"]).single().execute()
    name = profile.data.get("full_name") if profile.data else None
    result = await service.create_checkout_session(
        user_id=current_user["id"],
        email=current_user["email"],
        success_url=body.success_url,
        cancel_url=body.cancel_url,
        name=name,
    )
    return result


@router.post("/portal")
async def billing_portal(
    return_url: str,
    current_user: dict = Depends(require_active_subscription),
    supabase: Client = Depends(get_supabase),
):
    service = StripeService(supabase)
    portal_url = await service.create_portal_session(current_user["id"], return_url)
    return {"portal_url": portal_url}


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    supabase: Client = Depends(get_supabase),
):
    """Stripe webhook endpoint — must be unauthenticated."""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")
    service = StripeService(supabase)
    try:
        result = await service.handle_webhook(payload, sig_header)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/subscription")
async def get_subscription(
    current_user: dict = Depends(require_active_subscription),
    supabase: Client = Depends(get_supabase),
):
    resp = (
        supabase.table("subscriptions")
        .select("*")
        .eq("user_id", current_user["id"])
        .single()
        .execute()
    )
    if not resp.data:
        raise HTTPException(status_code=404, detail="No subscription")
    data = resp.data
    # Mask sensitive fields
    data.pop("stripe_customer_id", None)
    return data
