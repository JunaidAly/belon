"""Resend.com email service."""
from __future__ import annotations
import logging
import resend
from config import settings

logger = logging.getLogger(__name__)
resend.api_key = settings.RESEND_API_KEY


class EmailService:
    def __init__(self):
        self.from_email = settings.RESEND_FROM_EMAIL
        self.from_name = settings.RESEND_FROM_NAME

    async def send_welcome(self, to: str, name: str, trial_end: str) -> bool:
        try:
            resend.Emails.send({
                "from": f"{self.from_name} <{self.from_email}>",
                "to": [to],
                "subject": "Welcome to Belon — Your AI CRM Copilot is Live",
                "html": f"""
                <div style="font-family: sans-serif; max-width: 600px; margin: 0 auto; background: #080808; color: #fff; padding: 40px; border-radius: 16px;">
                  <h1 style="color: #f97316; margin-bottom: 8px;">Welcome to Belon, {name}!</h1>
                  <p style="color: rgba(255,255,255,0.7); font-size: 16px;">Your 5-day free trial is active and your AI pipeline agent is ready.</p>
                  <div style="background: rgba(249,115,22,0.1); border: 1px solid rgba(249,115,22,0.2); border-radius: 12px; padding: 20px; margin: 24px 0;">
                    <p style="color: #f97316; margin: 0; font-weight: 600;">Trial ends: {trial_end}</p>
                    <p style="color: rgba(255,255,255,0.6); margin: 8px 0 0 0; font-size: 14px;">After trial: $1,000/year. Cancel anytime before {trial_end}.</p>
                  </div>
                  <a href="{settings.FRONTEND_URL}/control-center" style="display: inline-block; background: #f97316; color: #000; padding: 14px 28px; border-radius: 12px; text-decoration: none; font-weight: 600; margin-top: 8px;">Open Belon →</a>
                  <p style="color: rgba(255,255,255,0.4); font-size: 13px; margin-top: 32px;">Need help? Reply to this email.</p>
                </div>
                """,
            })
            return True
        except Exception as e:
            logger.error(f"Welcome email failed: {e}")
            return False

    async def send_notification(self, to: str, subject: str, body: str, context: dict = None) -> bool:
        try:
            company = (context or {}).get("company_name", "")
            html_body = body.replace("\n", "<br>")
            resend.Emails.send({
                "from": f"{self.from_name} <{self.from_email}>",
                "to": [to],
                "subject": subject,
                "html": f"""
                <div style="font-family: sans-serif; max-width: 600px; margin: 0 auto; background: #080808; color: #fff; padding: 32px; border-radius: 12px;">
                  <p style="color: #f97316; font-size: 13px; margin-bottom: 8px;">BELON AI ALERT</p>
                  <h2 style="margin: 0 0 16px 0;">{subject}</h2>
                  <p style="color: rgba(255,255,255,0.7); line-height: 1.6;">{html_body}</p>
                  <a href="{settings.FRONTEND_URL}/control-center" style="display: inline-block; background: #f97316; color: #000; padding: 12px 24px; border-radius: 10px; text-decoration: none; font-weight: 600; margin-top: 16px;">View in Belon →</a>
                </div>
                """,
            })
            return True
        except Exception as e:
            logger.error(f"Notification email failed: {e}")
            return False

    async def send_trial_ending(self, to: str, name: str, days_left: int) -> bool:
        try:
            resend.Emails.send({
                "from": f"{self.from_name} <{self.from_email}>",
                "to": [to],
                "subject": f"Your Belon trial ends in {days_left} day{'s' if days_left != 1 else ''}",
                "html": f"""
                <div style="font-family: sans-serif; max-width: 600px; margin: 0 auto; background: #080808; color: #fff; padding: 40px; border-radius: 16px;">
                  <h2 style="color: #f97316;">Trial ending soon, {name}</h2>
                  <p style="color: rgba(255,255,255,0.7);">You have {days_left} day{'s' if days_left != 1 else ''} left on your Belon free trial.</p>
                  <p style="color: rgba(255,255,255,0.7);">Continue using Belon for $1,000/year — that's less than $3/day for a fully autonomous AI CRM pipeline.</p>
                  <a href="{settings.FRONTEND_URL}/billing" style="display: inline-block; background: #f97316; color: #000; padding: 14px 28px; border-radius: 12px; text-decoration: none; font-weight: 600; margin-top: 16px;">Upgrade Now →</a>
                </div>
                """,
            })
            return True
        except Exception as e:
            logger.error(f"Trial ending email failed: {e}")
            return False


email_service = EmailService()
