"""HubSpot two-way sync service."""
from __future__ import annotations
import logging
from datetime import datetime
from typing import Optional
import httpx

logger = logging.getLogger(__name__)

HUBSPOT_API_BASE = "https://api.hubapi.com"
HUBSPOT_AUTH_URL = "https://app.hubspot.com/oauth/authorize"
HUBSPOT_TOKEN_URL = "https://api.hubapi.com/oauth/v1/token"


class HubSpotService:
    def __init__(self, supabase, client_id: str, client_secret: str, redirect_uri: str):
        self.supabase = supabase
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri

    def get_auth_url(self, user_id: str) -> str:
        scopes = "crm.objects.contacts.read crm.objects.contacts.write crm.objects.deals.read crm.objects.deals.write crm.objects.companies.read"
        return (
            f"{HUBSPOT_AUTH_URL}"
            f"?client_id={self.client_id}"
            f"&redirect_uri={self.redirect_uri}"
            f"&scope={scopes.replace(' ', '%20')}"
            f"&state={user_id}"
        )

    async def exchange_code(self, code: str, user_id: str) -> dict:
        """Exchange OAuth code for tokens and save integration."""
        async with httpx.AsyncClient() as client:
            resp = await client.post(HUBSPOT_TOKEN_URL, data={
                "grant_type": "authorization_code",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "redirect_uri": self.redirect_uri,
                "code": code,
            })
            resp.raise_for_status()
            token_data = resp.json()

        # Get HubSpot account info
        access_token = token_data["access_token"]
        account_info = await self._get_account_info(access_token)

        # Upsert integration
        integration_data = {
            "user_id": user_id,
            "provider": "hubspot",
            "status": "connected",
            "access_token": access_token,
            "refresh_token": token_data.get("refresh_token"),
            "token_expires_at": None,
            "account_id": str(account_info.get("hub_id", "")),
            "account_name": account_info.get("hub_domain", "HubSpot"),
            "config": {"hub_id": account_info.get("hub_id")},
        }

        self.supabase.table("integrations").upsert(
            integration_data, on_conflict="user_id,provider"
        ).execute()

        return integration_data

    async def _get_account_info(self, access_token: str) -> dict:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{HUBSPOT_API_BASE}/oauth/v1/access-tokens/{access_token}",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            if resp.status_code == 200:
                return resp.json()
        return {}

    async def _get_access_token(self, user_id: str) -> Optional[str]:
        resp = (
            self.supabase.table("integrations")
            .select("access_token, refresh_token")
            .eq("user_id", user_id)
            .eq("provider", "hubspot")
            .single()
            .execute()
        )
        if not resp.data:
            return None
        return resp.data.get("access_token")

    async def sync_contacts(self, user_id: str, limit: int = 100) -> dict:
        """Pull contacts from HubSpot and upsert to Supabase."""
        access_token = await self._get_access_token(user_id)
        if not access_token:
            return {"error": "No HubSpot connection"}

        created = updated = failed = 0
        after = None
        batch_size = min(limit, 100)

        async with httpx.AsyncClient() as client:
            while True:
                params = {
                    "limit": batch_size,
                    "properties": "firstname,lastname,email,phone,company,jobtitle,hs_lead_status",
                }
                if after:
                    params["after"] = after

                resp = await client.get(
                    f"{HUBSPOT_API_BASE}/crm/v3/objects/contacts",
                    headers={"Authorization": f"Bearer {access_token}"},
                    params=params,
                )
                if resp.status_code != 200:
                    logger.error(f"HubSpot contacts error: {resp.text}")
                    break

                data = resp.json()
                results = data.get("results", [])

                for contact in results:
                    props = contact.get("properties", {})
                    try:
                        upsert_data = {
                            "user_id": user_id,
                            "external_id": contact["id"],
                            "source": "hubspot",
                            "first_name": props.get("firstname"),
                            "last_name": props.get("lastname"),
                            "email": props.get("email"),
                            "phone": props.get("phone"),
                            "company_name": props.get("company"),
                            "title": props.get("jobtitle"),
                            "status": self._map_hs_status(props.get("hs_lead_status", "lead")),
                        }
                        self.supabase.table("contacts").upsert(
                            upsert_data, on_conflict="user_id,external_id,source"
                        ).execute()
                        updated += 1
                    except Exception as e:
                        logger.error(f"Contact upsert failed: {e}")
                        failed += 1

                paging = data.get("paging", {})
                after = paging.get("next", {}).get("after")
                if not after or len(results) < batch_size:
                    break

        # Update last sync
        self.supabase.table("integrations").update({
            "last_sync_at": datetime.utcnow().isoformat(),
            "records_synced": created + updated,
            "status": "connected",
        }).eq("user_id", user_id).eq("provider", "hubspot").execute()

        return {"created": created, "updated": updated, "failed": failed}

    async def sync_deals(self, user_id: str, limit: int = 100) -> dict:
        """Pull deals from HubSpot and upsert to Supabase."""
        access_token = await self._get_access_token(user_id)
        if not access_token:
            return {"error": "No HubSpot connection"}

        created = updated = failed = 0
        after = None
        batch_size = min(limit, 100)

        async with httpx.AsyncClient() as client:
            while True:
                params = {
                    "limit": batch_size,
                    "properties": "dealname,amount,dealstage,closedate,hubspot_owner_id,hs_deal_stage_probability,notes_last_updated",
                    "associations": "contacts,companies",
                }
                if after:
                    params["after"] = after

                resp = await client.get(
                    f"{HUBSPOT_API_BASE}/crm/v3/objects/deals",
                    headers={"Authorization": f"Bearer {access_token}"},
                    params=params,
                )
                if resp.status_code != 200:
                    logger.error(f"HubSpot deals error: {resp.text}")
                    break

                data = resp.json()
                results = data.get("results", [])

                for deal in results:
                    props = deal.get("properties", {})
                    try:
                        amount = float(props.get("amount") or 0)
                        stage = self._map_hs_stage(props.get("dealstage", ""))
                        last_activity = props.get("notes_last_updated")
                        upsert_data = {
                            "user_id": user_id,
                            "external_id": deal["id"],
                            "source": "hubspot",
                            "name": props.get("dealname", f"Deal {deal['id']}"),
                            "value": amount,
                            "stage": stage,
                            "probability": int(float(props.get("hs_deal_stage_probability") or 20)),
                            "last_activity_at": last_activity,
                        }
                        if props.get("closedate"):
                            try:
                                cd = datetime.fromisoformat(props["closedate"][:10])
                                upsert_data["expected_close_date"] = cd.date().isoformat()
                            except ValueError:
                                pass

                        self.supabase.table("deals").upsert(
                            upsert_data, on_conflict="user_id,external_id,source"
                        ).execute()
                        updated += 1
                    except Exception as e:
                        logger.error(f"Deal upsert failed: {e}")
                        failed += 1

                paging = data.get("paging", {})
                after = paging.get("next", {}).get("after")
                if not after or len(results) < batch_size:
                    break

        self.supabase.table("integrations").update({
            "last_sync_at": datetime.utcnow().isoformat(),
            "status": "connected",
        }).eq("user_id", user_id).eq("provider", "hubspot").execute()

        return {"created": created, "updated": updated, "failed": failed}

    def _map_hs_status(self, hs_status: str) -> str:
        mapping = {
            "new": "lead", "open": "lead", "in_progress": "prospect",
            "open_deal": "prospect", "connected": "prospect",
            "unqualified": "unqualified", "bad timing": "unqualified",
        }
        return mapping.get(hs_status.lower() if hs_status else "", "lead")

    def _map_hs_stage(self, hs_stage: str) -> str:
        hs_stage = (hs_stage or "").lower()
        if any(k in hs_stage for k in ["appoint", "connect", "discover"]):
            return "discovery"
        if any(k in hs_stage for k in ["qualify", "present"]):
            return "qualification"
        if any(k in hs_stage for k in ["proposal", "quote"]):
            return "proposal"
        if any(k in hs_stage for k in ["negotiat", "decision"]):
            return "negotiation"
        if any(k in hs_stage for k in ["close", "won"]):
            return "closed_won"
        if "lost" in hs_stage:
            return "closed_lost"
        return "discovery"
