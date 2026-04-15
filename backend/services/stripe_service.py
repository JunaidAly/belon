"""Stripe billing service — 5-day trial + $1,000/year plan."""
from __future__ import annotations
import logging
import stripe
from config import settings

logger = logging.getLogger(__name__)
stripe.api_key = settings.STRIPE_SECRET_KEY


class StripeService:
    def __init__(self, supabase):
        self.supabase = supabase

    async def get_or_create_customer(self, user_id: str, email: str, name: str = None) -> str:
        """Get or create Stripe customer, return customer_id."""
        # Check existing
        resp = (
            self.supabase.table("subscriptions")
            .select("stripe_customer_id")
            .eq("user_id", user_id)
            .single()
            .execute()
        )
        if resp.data and resp.data.get("stripe_customer_id"):
            return resp.data["stripe_customer_id"]

        # Create new
        customer = stripe.Customer.create(
            email=email,
            name=name,
            metadata={"user_id": user_id},
        )

        # Update subscription record
        self.supabase.table("subscriptions").update({
            "stripe_customer_id": customer.id,
        }).eq("user_id", user_id).execute()

        return customer.id

    async def create_checkout_session(
        self,
        user_id: str,
        email: str,
        success_url: str,
        cancel_url: str,
        name: str = None,
    ) -> dict:
        """Create Stripe Checkout session with 5-day trial."""
        customer_id = await self.get_or_create_customer(user_id, email, name)

        session = stripe.checkout.Session.create(
            customer=customer_id,
            mode="subscription",
            line_items=[{
                "price": settings.STRIPE_PRICE_ID,
                "quantity": 1,
            }],
            subscription_data={
                "trial_period_days": settings.STRIPE_TRIAL_DAYS,
                "metadata": {"user_id": user_id},
            },
            success_url=success_url + "?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=cancel_url,
            allow_promotion_codes=True,
            metadata={"user_id": user_id},
        )

        return {
            "checkout_url": session.url,
            "session_id": session.id,
        }

    async def create_portal_session(self, user_id: str, return_url: str) -> str:
        """Create Stripe Customer Portal session."""
        resp = (
            self.supabase.table("subscriptions")
            .select("stripe_customer_id")
            .eq("user_id", user_id)
            .single()
            .execute()
        )
        if not resp.data or not resp.data.get("stripe_customer_id"):
            raise ValueError("No Stripe customer found")

        portal = stripe.billing_portal.Session.create(
            customer=resp.data["stripe_customer_id"],
            return_url=return_url,
        )
        return portal.url

    async def handle_webhook(self, payload: bytes, sig_header: str) -> dict:
        """Process Stripe webhook events."""
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Webhook signature invalid: {e}")
            raise ValueError("Invalid signature")

        event_type = event["type"]
        data = event["data"]["object"]

        handlers = {
            "customer.subscription.created": self._on_subscription_created,
            "customer.subscription.updated": self._on_subscription_updated,
            "customer.subscription.deleted": self._on_subscription_deleted,
            "invoice.payment_succeeded": self._on_payment_succeeded,
            "invoice.payment_failed": self._on_payment_failed,
            "customer.subscription.trial_will_end": self._on_trial_ending,
        }

        handler = handlers.get(event_type)
        if handler:
            await handler(data)
            logger.info(f"Handled webhook: {event_type}")
        else:
            logger.debug(f"Unhandled webhook: {event_type}")

        return {"received": True, "event_type": event_type}

    async def _on_subscription_created(self, sub: dict) -> None:
        user_id = sub.get("metadata", {}).get("user_id")
        if not user_id:
            return
        self._update_subscription(user_id, sub)

    async def _on_subscription_updated(self, sub: dict) -> None:
        user_id = sub.get("metadata", {}).get("user_id")
        if not user_id:
            # Try to find by customer_id
            resp = (
                self.supabase.table("subscriptions")
                .select("user_id")
                .eq("stripe_customer_id", sub.get("customer"))
                .single()
                .execute()
            )
            if resp.data:
                user_id = resp.data["user_id"]
        if user_id:
            self._update_subscription(user_id, sub)

    async def _on_subscription_deleted(self, sub: dict) -> None:
        user_id = sub.get("metadata", {}).get("user_id")
        if not user_id:
            resp = (
                self.supabase.table("subscriptions")
                .select("user_id")
                .eq("stripe_subscription_id", sub.get("id"))
                .single()
                .execute()
            )
            if resp.data:
                user_id = resp.data["user_id"]
        if user_id:
            self.supabase.table("subscriptions").update({
                "status": "canceled",
                "stripe_subscription_id": sub.get("id"),
            }).eq("user_id", user_id).execute()

    async def _on_payment_succeeded(self, invoice: dict) -> None:
        sub_id = invoice.get("subscription")
        if sub_id:
            resp = (
                self.supabase.table("subscriptions")
                .select("user_id")
                .eq("stripe_subscription_id", sub_id)
                .single()
                .execute()
            )
            if resp.data:
                self.supabase.table("subscriptions").update({
                    "status": "active",
                }).eq("user_id", resp.data["user_id"]).execute()

    async def _on_payment_failed(self, invoice: dict) -> None:
        sub_id = invoice.get("subscription")
        if sub_id:
            resp = (
                self.supabase.table("subscriptions")
                .select("user_id")
                .eq("stripe_subscription_id", sub_id)
                .single()
                .execute()
            )
            if resp.data:
                self.supabase.table("subscriptions").update({
                    "status": "past_due",
                }).eq("user_id", resp.data["user_id"]).execute()

    async def _on_trial_ending(self, sub: dict) -> None:
        # Signal that trial is ending — could trigger email
        user_id = sub.get("metadata", {}).get("user_id")
        logger.info(f"Trial ending for user {user_id}")

    def _update_subscription(self, user_id: str, sub: dict) -> None:
        status = sub.get("status", "trialing")
        period_start = sub.get("current_period_start")
        period_end = sub.get("current_period_end")

        import datetime as dt
        update_data = {
            "stripe_subscription_id": sub.get("id"),
            "stripe_price_id": sub.get("items", {}).get("data", [{}])[0].get("price", {}).get("id") if sub.get("items") else None,
            "status": status,
            "cancel_at_period_end": sub.get("cancel_at_period_end", False),
        }
        if period_start:
            update_data["current_period_start"] = dt.datetime.fromtimestamp(period_start).isoformat()
        if period_end:
            update_data["current_period_end"] = dt.datetime.fromtimestamp(period_end).isoformat()
        if sub.get("trial_end"):
            update_data["trial_end"] = dt.datetime.fromtimestamp(sub["trial_end"]).isoformat()

        self.supabase.table("subscriptions").update(update_data).eq("user_id", user_id).execute()
