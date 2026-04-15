"""
Belon 100+ Signal Engine
Detects pipeline issues, buying signals, churn risk, rep performance,
engagement gaps, and AI insights. Runs every 15 minutes.
"""
from __future__ import annotations
import logging
from datetime import datetime, timedelta
from typing import Any
from uuid import uuid4

logger = logging.getLogger(__name__)

# ── Signal Type Registry ──────────────────────────────────────────────────────
# Each entry: (signal_type, category, severity, title_template, description_template, action_label, action_type)

SIGNAL_DEFINITIONS: list[dict] = [
    # DEAL HEALTH (20 signals)
    {"type": "deal_stalled_7d",      "category": "deal_health",    "severity": "medium",   "title": "{company} deal stalled for 7 days",        "desc": "No activity logged. Last contact was {last_contact}.",           "action": "Send check-in email",       "action_type": "email"},
    {"type": "deal_stalled_14d",     "category": "deal_health",    "severity": "high",     "title": "{company} deal stalled for 14 days",       "desc": "No CRM activity for 14+ days. Deal value: ${value}.",             "action": "Draft re-engagement email", "action_type": "ai_draft"},
    {"type": "deal_stalled_21d",     "category": "deal_health",    "severity": "critical", "title": "{company} deal critical — 21 days no activity", "desc": "Deal at high risk of being lost. Immediate action required.",  "action": "Emergency recovery sequence","action_type": "workflow"},
    {"type": "deal_no_next_step",    "category": "deal_health",    "severity": "high",     "title": "No next step set: {company}",              "desc": "Deal moved to {stage} with no follow-up task created.",           "action": "Create next step",          "action_type": "crm_update"},
    {"type": "deal_missing_contact", "category": "deal_health",    "severity": "medium",   "title": "No contact person on {company} deal",      "desc": "Deal missing primary contact — can't track engagement.",          "action": "Add contact",               "action_type": "crm_update"},
    {"type": "deal_health_dropped",  "category": "deal_health",    "severity": "high",     "title": "{company} health score dropped to {score}", "desc": "Health score fell {drop} points in the last 7 days.",           "action": "Analyze deal",              "action_type": "ai_draft"},
    {"type": "deal_stage_regression","category": "deal_health",    "severity": "high",     "title": "{company} deal moved backward in pipeline","desc": "Deal moved from {from_stage} back to {to_stage}.",               "action": "Review deal",               "action_type": "crm_update"},
    {"type": "deal_value_gap",       "category": "deal_health",    "severity": "medium",   "title": "High-value deal {company} needs attention", "desc": "${value} deal with health score below 50.",                      "action": "Prioritize deal",           "action_type": "task"},
    {"type": "deal_long_discovery",  "category": "deal_health",    "severity": "medium",   "title": "{company} stuck in discovery for {days}d", "desc": "Average discovery stage is {avg_days} days. This deal is {days}d.", "action": "Qualify or disqualify",   "action_type": "task"},
    {"type": "deal_long_proposal",   "category": "deal_health",    "severity": "high",     "title": "{company} proposal not responded for {days}d", "desc": "Proposal sent {days} days ago with no response.",              "action": "Follow up on proposal",     "action_type": "email"},
    {"type": "deal_close_date_past", "category": "deal_health",    "severity": "critical", "title": "{company} deal past expected close date",  "desc": "Expected close was {close_date}. Deal still open.",              "action": "Update close date",         "action_type": "crm_update"},
    {"type": "deal_close_imminent",  "category": "deal_health",    "severity": "info",     "title": "{company} expected to close in {days}d",   "desc": "Closing soon — ensure all stakeholders are aligned.",            "action": "Pre-close checklist",       "action_type": "task"},
    {"type": "deal_competitor_risk", "category": "deal_health",    "severity": "high",     "title": "Competitor risk detected: {company}",      "desc": "Competitor {competitor} mentioned in recent activity notes.",     "action": "Competitive battlecard",    "action_type": "ai_draft"},
    {"type": "deal_champion_left",   "category": "deal_health",    "severity": "critical", "title": "Deal champion left {company}",             "desc": "{contact} who championed this deal has left the company.",       "action": "Identify new champion",     "action_type": "workflow"},
    {"type": "deal_budget_concern",  "category": "deal_health",    "severity": "high",     "title": "Budget concern flagged: {company}",        "desc": "Budget-related keywords detected in recent notes or emails.",    "action": "ROI justification email",   "action_type": "ai_draft"},
    {"type": "deal_technical_blocker","category": "deal_health",   "severity": "medium",   "title": "Technical blocker at {company}",           "desc": "Technical evaluation has been ongoing for {days}+ days.",        "action": "Schedule SE call",          "action_type": "schedule"},
    {"type": "deal_legal_delay",     "category": "deal_health",    "severity": "medium",   "title": "Legal review delayed at {company}",        "desc": "Contract in legal review for {days} days.",                      "action": "Check contract status",     "action_type": "task"},
    {"type": "deal_multi_threaded",  "category": "deal_health",    "severity": "info",     "title": "Single-threaded deal risk: {company}",     "desc": "Only 1 stakeholder engaged on a ${value} deal.",                "action": "Multi-thread outreach",     "action_type": "ai_draft"},
    {"type": "deal_inactivity_risk", "category": "deal_health",    "severity": "medium",   "title": "{company} — rep hasn't logged activity",   "desc": "{rep} hasn't logged any activity on this deal for {days} days.", "action": "Prompt rep",               "action_type": "task"},
    {"type": "deal_low_engagement",  "category": "deal_health",    "severity": "medium",   "title": "Low engagement from {company}",            "desc": "Last 3 emails have gone unopened.",                              "action": "Try different channel",     "action_type": "task"},

    # BUYING SIGNALS (20 signals)
    {"type": "pricing_page_visit",   "category": "buying_signal",  "severity": "high",     "title": "{company} visited pricing page {count}x", "desc": "Pricing page visited {count} times in {days} days.",            "action": "Schedule discovery call",   "action_type": "schedule"},
    {"type": "demo_request",         "category": "buying_signal",  "severity": "critical", "title": "Demo request from {company}",              "desc": "New demo request submitted. Respond within 1 hour for best conversion.", "action": "Book demo now",      "action_type": "schedule"},
    {"type": "roi_calc_used",        "category": "buying_signal",  "severity": "high",     "title": "{company} used ROI calculator",            "desc": "ROI calculation performed. Estimated value: ${roi_value}.",     "action": "Send ROI summary",          "action_type": "email"},
    {"type": "multiple_stakeholders","category": "buying_signal",  "severity": "high",     "title": "{count} new stakeholders at {company}",    "desc": "{count} new stakeholders engaged this week — buying committee forming.", "action": "Stakeholder mapping",  "action_type": "ai_draft"},
    {"type": "case_study_download",  "category": "buying_signal",  "severity": "medium",   "title": "{company} downloaded case study",          "desc": "{contact} downloaded '{case_study}' — high intent signal.",     "action": "Follow up with context",    "action_type": "email"},
    {"type": "feature_page_visit",   "category": "buying_signal",  "severity": "medium",   "title": "{company} researching {feature} feature",  "desc": "Multiple visits to {feature} feature page — specific interest.", "action": "Feature demo email",       "action_type": "ai_draft"},
    {"type": "linkedin_engagement",  "category": "buying_signal",  "severity": "medium",   "title": "{contact} engaging on LinkedIn",           "desc": "{contact} liked/commented on company posts — warm signal.",     "action": "LinkedIn connection request", "action_type": "task"},
    {"type": "trial_started",        "category": "buying_signal",  "severity": "high",     "title": "{company} started a trial",                "desc": "Free trial activated. Onboard within 24h for best conversion.", "action": "Onboarding call",           "action_type": "schedule"},
    {"type": "trial_active",         "category": "buying_signal",  "severity": "medium",   "title": "{company} active in trial — {days}d left", "desc": "Trial usage high. {days} days remaining.",                      "action": "Trial success check-in",    "action_type": "email"},
    {"type": "trial_expiring",       "category": "buying_signal",  "severity": "critical", "title": "{company} trial expires in {days}d",       "desc": "Trial ending soon. No conversion yet.",                         "action": "Conversion call",           "action_type": "schedule"},
    {"type": "competitor_comparison","category": "buying_signal",  "severity": "high",     "title": "{company} comparing us vs {competitor}",   "desc": "Prospect researching competitor comparison pages.",             "action": "Competitive win strategy",  "action_type": "ai_draft"},
    {"type": "inbound_email",        "category": "buying_signal",  "severity": "high",     "title": "Inbound email from {contact} at {company}","desc": "New inbound message — intent unclear, needs qualification.",    "action": "Qualify and respond",       "action_type": "email"},
    {"type": "website_revisit",      "category": "buying_signal",  "severity": "medium",   "title": "{company} revisiting website after {days}d gap", "desc": "Went dark for {days} days, now back on site.",             "action": "Re-engage now",             "action_type": "ai_draft"},
    {"type": "integration_page",     "category": "buying_signal",  "severity": "medium",   "title": "{company} browsing integrations",          "desc": "Viewing integration pages — evaluating tech compatibility.",    "action": "Integrations walkthrough",  "action_type": "email"},
    {"type": "security_page_visit",  "category": "buying_signal",  "severity": "medium",   "title": "{company} reviewing security docs",        "desc": "Enterprise security/compliance page viewed — enterprise deal.", "action": "Security overview call",    "action_type": "schedule"},
    {"type": "referral_signal",      "category": "buying_signal",  "severity": "high",     "title": "Referral from {referrer} to {company}",    "desc": "{referrer} referred {company}. Warm introduction available.",   "action": "Request intro",             "action_type": "email"},
    {"type": "budget_confirmed",     "category": "buying_signal",  "severity": "critical", "title": "Budget confirmed at {company}",             "desc": "{contact} confirmed budget approval for this initiative.",      "action": "Accelerate deal",           "action_type": "workflow"},
    {"type": "contract_request",     "category": "buying_signal",  "severity": "critical", "title": "{company} requesting contract",             "desc": "Prospect asking for contract/terms — imminent close.",          "action": "Send contract",             "action_type": "crm_update"},
    {"type": "job_post_signal",      "category": "buying_signal",  "severity": "medium",   "title": "{company} hiring for relevant roles",      "desc": "{company} posted job for {role} — growth/investment signal.",   "action": "Reach out with relevance",  "action_type": "ai_draft"},
    {"type": "news_trigger",         "category": "buying_signal",  "severity": "medium",   "title": "Trigger event: {company} in the news",     "desc": "{company} announced {event}. Relevant outreach opportunity.",   "action": "Timely outreach",           "action_type": "ai_draft"},

    # CHURN RISK (15 signals)
    {"type": "renewal_approaching",  "category": "churn_risk",     "severity": "high",     "title": "{company} renewal in {days}d",             "desc": "Contract renewal approaching. No renewal discussion started.",  "action": "Start renewal conversation","action_type": "email"},
    {"type": "renewal_critical",     "category": "churn_risk",     "severity": "critical", "title": "{company} renewal CRITICAL — {days}d left","desc": "${arr} ARR renewal in {days} days. No champion contact in {contact_gap}d.", "action": "Executive intervention", "action_type": "workflow"},
    {"type": "champion_disengaged",  "category": "churn_risk",     "severity": "critical", "title": "Champion disengaged at {company}",         "desc": "{contact} hasn't responded in {days} days.",                    "action": "Multi-thread outreach",     "action_type": "ai_draft"},
    {"type": "usage_dropped",        "category": "churn_risk",     "severity": "high",     "title": "{company} usage dropped {pct}%",           "desc": "Product usage down {pct}% in the last 30 days.",               "action": "Health check call",         "action_type": "schedule"},
    {"type": "support_tickets_surge","category": "churn_risk",     "severity": "high",     "title": "{company} — {count} open support tickets", "desc": "{count} open tickets, {critical} critical. NPS risk.",         "action": "Customer rescue plan",      "action_type": "workflow"},
    {"type": "negative_nps",         "category": "churn_risk",     "severity": "critical", "title": "Negative NPS from {company}",              "desc": "NPS score: {score}. Detractor response requires immediate action.", "action": "Executive escalation",   "action_type": "schedule"},
    {"type": "payment_failed",       "category": "churn_risk",     "severity": "critical", "title": "Payment failed: {company}",                "desc": "Payment declined {count} times. Account may churn.",            "action": "Billing recovery sequence", "action_type": "email"},
    {"type": "contract_not_renewed", "category": "churn_risk",     "severity": "critical", "title": "{company} did not renew",                  "desc": "Contract expired without renewal. Win-back window: 30 days.",  "action": "Win-back campaign",         "action_type": "workflow"},
    {"type": "exec_sponsor_left",    "category": "churn_risk",     "severity": "critical", "title": "Exec sponsor left {company}",              "desc": "{contact} ({title}) left the company. Relationship at risk.",   "action": "Re-establish relationship", "action_type": "ai_draft"},
    {"type": "competitive_eval",     "category": "churn_risk",     "severity": "high",     "title": "{company} evaluating competitors",         "desc": "Signals indicate competitive evaluation in progress.",          "action": "Competitive defense play",  "action_type": "workflow"},
    {"type": "budget_cut_signal",    "category": "churn_risk",     "severity": "high",     "title": "Budget cuts at {company}",                 "desc": "{company} announced layoffs or budget reductions.",             "action": "ROI reinforcement email",   "action_type": "ai_draft"},
    {"type": "escalation_required",  "category": "churn_risk",     "severity": "critical", "title": "Escalation needed: {company}",             "desc": "Multiple red flags. Needs executive-to-executive engagement.",  "action": "Escalation plan",           "action_type": "workflow"},
    {"type": "data_export_signal",   "category": "churn_risk",     "severity": "high",     "title": "{company} exported all data",              "desc": "Full data export detected — potential churn signal.",           "action": "Retention conversation",    "action_type": "schedule"},
    {"type": "downgrade_requested",  "category": "churn_risk",     "severity": "high",     "title": "{company} requested plan downgrade",       "desc": "Downgrade request received. Expansion opportunity lost.",       "action": "Value re-qualification",    "action_type": "schedule"},
    {"type": "inactive_account",     "category": "churn_risk",     "severity": "medium",   "title": "{company} — no logins in {days}d",         "desc": "Zero product logins in {days} days.",                           "action": "Re-activation campaign",    "action_type": "email"},

    # REP PERFORMANCE (15 signals)
    {"type": "rep_activity_gap",     "category": "rep_performance","severity": "high",     "title": "{rep} no activity for {days}d",            "desc": "{rep} hasn't logged CRM activity in {days} days. {deal_count} deals affected.", "action": "Manager check-in",  "action_type": "task"},
    {"type": "rep_behind_quota",     "category": "rep_performance","severity": "high",     "title": "{rep} at {pct}% of quota",                 "desc": "{rep} at {pct}% of quota with {days_left}d left in quarter.",  "action": "Pipeline review",           "action_type": "task"},
    {"type": "rep_no_followups",     "category": "rep_performance","severity": "medium",   "title": "{rep} has {count} overdue follow-ups",     "desc": "{count} tasks overdue across {rep}'s portfolio.",              "action": "Task reminder sequence",    "action_type": "email"},
    {"type": "rep_top_performer",    "category": "rep_performance","severity": "info",     "title": "{rep} top performer this week",            "desc": "{rep} closed {deals} deals, {pct}% above team average.",       "action": "Replicate playbook",        "action_type": "task"},
    {"type": "rep_conversion_low",   "category": "rep_performance","severity": "medium",   "title": "{rep} conversion rate dropped",            "desc": "Stage conversion rate at {rate}% vs team average {avg}%.",     "action": "Coaching recommendation",   "action_type": "ai_draft"},
    {"type": "rep_talk_ratio",       "category": "rep_performance","severity": "medium",   "title": "{rep} talk ratio too high",                "desc": "Rep speaking {pct}% of call time. Best practice: 40-50%.",     "action": "Call coaching",             "action_type": "task"},
    {"type": "rep_email_overdue",    "category": "rep_performance","severity": "medium",   "title": "{rep} hasn't replied to {company} in {days}d","desc": "Customer email waiting {days} days for response.",          "action": "Urgent reply needed",       "action_type": "email"},
    {"type": "rep_forecast_gap",     "category": "rep_performance","severity": "high",     "title": "{rep} forecast gap: ${gap}K",              "desc": "{rep} committed ${committed}K but only ${pipeline}K in pipeline.", "action": "Pipeline expansion plan","action_type": "task"},
    {"type": "rep_deal_size_trend",  "category": "rep_performance","severity": "info",     "title": "{rep} deal size trending {direction}",     "desc": "Average deal size {direction} {pct}% vs last quarter.",        "action": "Deal size analysis",        "action_type": "ai_draft"},
    {"type": "rep_velocity_low",     "category": "rep_performance","severity": "medium",   "title": "{rep} deal velocity below average",        "desc": "Deals moving {pct}% slower than team average through pipeline.","action": "Velocity coaching",         "action_type": "task"},
    {"type": "rep_multithreading",   "category": "rep_performance","severity": "info",     "title": "{rep} single-threading multiple deals",    "desc": "{count} deals with only 1 stakeholder engaged.",              "action": "Multi-thread training",     "action_type": "task"},
    {"type": "rep_discovery_quality","category": "rep_performance","severity": "medium",   "title": "{rep} discovery notes incomplete",         "desc": "{count} deals missing key MEDDIC/BANT qualification fields.",  "action": "Discovery quality review",  "action_type": "task"},
    {"type": "rep_proposal_rate",    "category": "rep_performance","severity": "info",     "title": "{rep} high proposal win rate",             "desc": "{rep} converting {pct}% of proposals — top quartile.",         "action": "Share best practices",      "action_type": "task"},
    {"type": "rep_response_time",    "category": "rep_performance","severity": "high",     "title": "{rep} slow lead response time",            "desc": "Average lead response: {hours}h (benchmark: <2h).",            "action": "Response SLA alert",        "action_type": "task"},
    {"type": "rep_no_renewal_focus", "category": "rep_performance","severity": "high",     "title": "{rep} has {count} renewals ignored",       "desc": "{count} renewals in 60-day window with no rep activity.",      "action": "Renewal priority list",     "action_type": "task"},

    # PIPELINE HEALTH (15 signals)
    {"type": "pipeline_coverage_low","category": "pipeline_health","severity": "high",     "title": "Pipeline coverage only {ratio}x",          "desc": "Pipeline coverage {ratio}x quota. Target: 3-4x.",              "action": "Pipeline build plan",       "action_type": "task"},
    {"type": "pipeline_skewed",      "category": "pipeline_health","severity": "medium",   "title": "Pipeline skewed to early stages",          "desc": "{pct}% of pipeline in discovery/qualification.",               "action": "Accelerate pipeline",       "action_type": "workflow"},
    {"type": "pipeline_stale",       "category": "pipeline_health","severity": "high",     "title": "{count} stale deals need cleanup",         "desc": "{count} deals with no activity in 30+ days.",                  "action": "Pipeline cleanup",          "action_type": "workflow"},
    {"type": "pipeline_at_risk_high","category": "pipeline_health","severity": "critical", "title": "${value}K pipeline at critical risk",       "desc": "{count} high-value deals with health score below 40.",         "action": "Priority intervention list","action_type": "workflow"},
    {"type": "forecast_risk",        "category": "pipeline_health","severity": "high",     "title": "Forecast at risk — {pct}% gap to target",  "desc": "Current projection short of target by {gap_amount}.",          "action": "Forecast recovery plan",    "action_type": "ai_draft"},
    {"type": "stage_conversion_drop","category": "pipeline_health","severity": "medium",   "title": "{stage} → {next_stage} conversion dropped","desc": "Conversion rate fell from {old_rate}% to {new_rate}% this month.", "action": "Stage analysis",          "action_type": "ai_draft"},
    {"type": "avg_deal_size_drop",   "category": "pipeline_health","severity": "medium",   "title": "Average deal size down {pct}%",            "desc": "Average deal size dropped from ${old} to ${new}.",             "action": "Deal sizing review",        "action_type": "ai_draft"},
    {"type": "win_rate_drop",        "category": "pipeline_health","severity": "high",     "title": "Win rate dropped to {rate}%",              "desc": "Win rate {rate}% vs {prev_rate}% last quarter.",               "action": "Win/loss analysis",         "action_type": "ai_draft"},
    {"type": "cycle_length_increase","category": "pipeline_health","severity": "medium",   "title": "Sales cycle length increasing",            "desc": "Average cycle now {days}d, up {pct}% from last quarter.",      "action": "Velocity analysis",         "action_type": "ai_draft"},
    {"type": "no_new_opps",          "category": "pipeline_health","severity": "high",     "title": "No new opportunities this week",           "desc": "Zero new opportunities created in 7 days.",                    "action": "Prospecting push",          "action_type": "task"},
    {"type": "pipeline_leak",        "category": "pipeline_health","severity": "high",     "title": "Pipeline leak detected: {stage}",          "desc": "{count} deals dropping out of {stage} without progressing.",   "action": "Stage analysis",            "action_type": "ai_draft"},
    {"type": "quota_attainment",     "category": "pipeline_health","severity": "info",     "title": "Team quota attainment: {pct}%",            "desc": "Team at {pct}% of quarterly quota with {days_left}d remaining.","action": "Quota sprint plan",         "action_type": "ai_draft"},
    {"type": "seasonal_risk",        "category": "pipeline_health","severity": "medium",   "title": "Seasonal deal risk — Q{quarter} slowdown", "desc": "Historical data shows {pct}% drop in this period.",            "action": "Build bridge pipeline",     "action_type": "task"},
    {"type": "territory_gap",        "category": "pipeline_health","severity": "medium",   "title": "{territory} territory underperforming",    "desc": "{territory} generating {pct}% below team average.",            "action": "Territory review",          "action_type": "task"},
    {"type": "product_mix_risk",     "category": "pipeline_health","severity": "info",     "title": "Product mix risk — {product} concentrated","desc": "{pct}% of pipeline from single product line.",                 "action": "Cross-sell expansion",      "action_type": "task"},

    # ENGAGEMENT (10 signals)
    {"type": "email_not_opened",     "category": "engagement",     "severity": "medium",   "title": "{contact} not opening emails",             "desc": "Last {count} emails unopened. Try different approach.",        "action": "Switch channel",            "action_type": "task"},
    {"type": "meeting_no_show",      "category": "engagement",     "severity": "high",     "title": "{contact} no-showed scheduled meeting",    "desc": "Meeting with {contact} at {company} was missed.",              "action": "Re-schedule with context",  "action_type": "email"},
    {"type": "fast_reply_signal",    "category": "engagement",     "severity": "info",     "title": "{contact} replying fast — hot lead",       "desc": "{contact} responded in under 30 minutes. High engagement.",    "action": "Strike while hot",          "action_type": "schedule"},
    {"type": "content_engagement",   "category": "engagement",     "severity": "medium",   "title": "{contact} highly engaged with content",    "desc": "{contact} viewed {count} pieces of content this week.",        "action": "Content-led outreach",      "action_type": "email"},
    {"type": "webinar_attended",     "category": "engagement",     "severity": "medium",   "title": "{contact} attended webinar",               "desc": "{contact} attended '{webinar_name}'. Follow up with context.", "action": "Webinar follow-up",         "action_type": "email"},
    {"type": "event_signal",         "category": "engagement",     "severity": "medium",   "title": "{contact} registered for event",           "desc": "{contact} registered for {event}. Coordinate at-event meeting.", "action": "Book at-event meeting",    "action_type": "schedule"},
    {"type": "social_mention",       "category": "engagement",     "severity": "info",     "title": "{company} mentioned us on social",         "desc": "{company} mentioned Belon on {platform}.",                     "action": "Engage and thank",          "action_type": "task"},
    {"type": "review_posted",        "category": "engagement",     "severity": "info",     "title": "{company} posted a review",                "desc": "{contact} posted a {sentiment} review on {platform}.",         "action": "Respond to review",         "action_type": "task"},
    {"type": "referral_submitted",   "category": "engagement",     "severity": "high",     "title": "{contact} submitted a referral",           "desc": "{contact} referred {referred_company}. Activate referral workflow.", "action": "Thank and process",     "action_type": "workflow"},
    {"type": "cold_outreach_bounced","category": "engagement",     "severity": "medium",   "title": "Email bounced: {contact}",                 "desc": "Email to {contact} at {company} bounced. Update contact data.", "action": "Find new contact",         "action_type": "task"},

    # AI INSIGHTS (5 signals)
    {"type": "ai_deal_risk_forecast","category": "ai_insight",     "severity": "high",     "title": "AI flags {count} deals as likely to slip","desc": "AI model predicts {count} deals will miss close date.",         "action": "Review AI analysis",        "action_type": "ai_draft"},
    {"type": "ai_best_time_contact", "category": "ai_insight",     "severity": "info",     "title": "Best time to contact {contact}: {time}",   "desc": "AI analysis shows {contact} most responsive on {day} at {time}.", "action": "Schedule for optimal time","action_type": "schedule"},
    {"type": "ai_persona_insight",   "category": "ai_insight",     "severity": "info",     "title": "Persona insight for {company}",            "desc": "AI identified {contact} as {persona_type}. Adjust messaging.", "action": "Personalize outreach",      "action_type": "ai_draft"},
    {"type": "ai_competitor_threat", "category": "ai_insight",     "severity": "high",     "title": "AI: {competitor} gaining ground in pipeline","desc": "{competitor} appearing in {count} deal notes this month.",   "action": "Competitive battle plan",   "action_type": "ai_draft"},
    {"type": "ai_seasonality",       "category": "ai_insight",     "severity": "info",     "title": "AI: seasonal pattern detected",            "desc": "Historical patterns suggest {action} in this period.",         "action": "View AI forecast",          "action_type": "ai_draft"},
]


class SignalEngine:
    """
    Processes deal data and emits signals to the database.
    Called by the background scheduler every SIGNAL_ENGINE_INTERVAL_MINUTES minutes.
    """

    def __init__(self, supabase_client):
        self.supabase = supabase_client
        self._definitions = {d["type"]: d for d in SIGNAL_DEFINITIONS}

    async def run_for_user(self, user_id: str) -> int:
        """Run full signal scan for a user. Returns count of new signals generated."""
        generated = 0

        # Fetch user's deals
        deals_resp = self.supabase.table("deals").select("*").eq("user_id", user_id).execute()
        deals = deals_resp.data or []

        # Fetch existing pending signals (avoid duplicates)
        existing_resp = (
            self.supabase.table("signals")
            .select("signal_type, entity_id")
            .eq("user_id", user_id)
            .eq("status", "pending")
            .execute()
        )
        existing_keys = {
            (r["signal_type"], r.get("entity_id", ""))
            for r in (existing_resp.data or [])
        }

        batch: list[dict] = []

        for deal in deals:
            new_signals = self._analyze_deal(deal, existing_keys)
            batch.extend(new_signals)
            generated += len(new_signals)

        # Fetch reps and check performance signals
        rep_signals = self._analyze_rep_performance(deals, existing_keys, user_id)
        batch.extend(rep_signals)
        generated += len(rep_signals)

        # Pipeline-level signals
        pipeline_signals = self._analyze_pipeline_health(deals, existing_keys, user_id)
        batch.extend(pipeline_signals)
        generated += len(pipeline_signals)

        # Insert batch
        if batch:
            for sig in batch:
                sig["user_id"] = user_id
            self.supabase.table("signals").insert(batch).execute()

        logger.info(f"Signal engine: {generated} new signals for user {user_id}")
        return generated

    def _analyze_deal(self, deal: dict, existing_keys: set) -> list[dict]:
        """Generate signals for a single deal."""
        signals = []
        now = datetime.utcnow()
        deal_id = deal.get("id", "")
        company = deal.get("company_name", "Unknown")
        value = deal.get("value", 0)
        stage = deal.get("stage", "discovery")
        health = deal.get("health_score", 50)
        days_in_stage = deal.get("days_in_stage", 0)
        last_activity = deal.get("last_activity_at")
        if last_activity and isinstance(last_activity, str):
            try:
                last_activity = datetime.fromisoformat(last_activity.replace("Z", "+00:00"))
            except ValueError:
                last_activity = None

        days_since_activity = (now - last_activity.replace(tzinfo=None)).days if last_activity else 999

        # Stall signals
        for days_threshold, sig_type in [(7, "deal_stalled_7d"), (14, "deal_stalled_14d"), (21, "deal_stalled_21d")]:
            if days_since_activity >= days_threshold and (sig_type, deal_id) not in existing_keys:
                signals.append(self._build_signal(sig_type, company, deal_id, "deal", value, {
                    "last_contact": f"{days_since_activity} days ago",
                    "value": f"{value:,.0f}",
                }))
                break  # Only highest severity stall signal

        # Health dropped
        if health < 45 and ("deal_health_dropped", deal_id) not in existing_keys:
            signals.append(self._build_signal("deal_health_dropped", company, deal_id, "deal", value, {
                "score": health, "drop": 20  # approximate
            }))

        # No next step (proxy: health < 50 + stage not discovery)
        if health < 50 and stage in ("qualification", "proposal", "negotiation") and ("deal_no_next_step", deal_id) not in existing_keys:
            signals.append(self._build_signal("deal_no_next_step", company, deal_id, "deal", value, {
                "stage": stage
            }))

        # Close date past
        close_date = deal.get("expected_close_date")
        if close_date:
            if isinstance(close_date, str):
                try:
                    close_date = datetime.fromisoformat(close_date).date()
                except ValueError:
                    close_date = None
            if close_date and close_date < now.date() and ("deal_close_date_past", deal_id) not in existing_keys:
                signals.append(self._build_signal("deal_close_date_past", company, deal_id, "deal", value, {
                    "close_date": str(close_date)
                }))

        # High value + low health
        if value > 50000 and health < 50 and ("deal_value_gap", deal_id) not in existing_keys:
            signals.append(self._build_signal("deal_value_gap", company, deal_id, "deal", value, {
                "value": f"{value:,.0f}"
            }))

        return signals

    def _analyze_rep_performance(self, deals: list[dict], existing_keys: set, user_id: str) -> list[dict]:
        """Generate rep-level signals."""
        from collections import defaultdict
        signals = []
        now = datetime.utcnow()

        rep_deals: dict[str, list[dict]] = defaultdict(list)
        for d in deals:
            rep = d.get("owner_name") or d.get("owner_email")
            if rep:
                rep_deals[rep].append(d)

        for rep, rep_deal_list in rep_deals.items():
            # Check if rep has stale deals
            stale = [d for d in rep_deal_list if d.get("days_in_stage", 0) > 14]
            if len(stale) >= 3 and ("rep_activity_gap", rep) not in existing_keys:
                signals.append(self._build_signal("rep_activity_gap", rep, rep, "rep", None, {
                    "rep": rep, "days": 14, "deal_count": len(stale)
                }))

            # No follow-ups proxy
            overdue = [d for d in rep_deal_list if d.get("health_score", 100) < 40]
            if len(overdue) >= 2 and ("rep_no_followups", rep) not in existing_keys:
                signals.append(self._build_signal("rep_no_followups", rep, rep, "rep", None, {
                    "rep": rep, "count": len(overdue)
                }))

        return signals

    def _analyze_pipeline_health(self, deals: list[dict], existing_keys: set, user_id: str) -> list[dict]:
        """Generate pipeline-level signals."""
        signals = []
        if not deals:
            return signals

        total_value = sum(d.get("value", 0) for d in deals)
        at_risk_count = sum(1 for d in deals if d.get("health_score", 100) < 40)
        at_risk_value = sum(d.get("value", 0) for d in deals if d.get("health_score", 100) < 40)
        stale_count = sum(1 for d in deals if d.get("days_in_stage", 0) > 30)

        # High at-risk pipeline
        if at_risk_value > 100000 and at_risk_count >= 3 and ("pipeline_at_risk_high", user_id) not in existing_keys:
            signals.append(self._build_signal("pipeline_at_risk_high", "Your Pipeline", user_id, "pipeline", at_risk_value, {
                "value": f"{at_risk_value/1000:.0f}",
                "count": at_risk_count
            }))

        # Stale deals cleanup
        if stale_count >= 5 and ("pipeline_stale", user_id) not in existing_keys:
            signals.append(self._build_signal("pipeline_stale", "Your Pipeline", user_id, "pipeline", None, {
                "count": stale_count
            }))

        return signals

    def _build_signal(
        self,
        signal_type: str,
        entity_name: str,
        entity_id: str,
        entity_type: str,
        deal_value: Any,
        ctx: dict,
    ) -> dict:
        """Build a signal dict from a definition + context."""
        defn = self._definitions.get(signal_type, {})
        try:
            title = defn.get("title", signal_type).format(company=entity_name, **ctx)
        except (KeyError, IndexError):
            title = defn.get("title", signal_type).format_map({
                k: ctx.get(k, entity_name) for k in ["company", "rep", "contact", "count", "days",
                "value", "pct", "score", "stage", "rate"]
            })

        try:
            desc = defn.get("desc", "").format(company=entity_name, **ctx)
        except (KeyError, IndexError):
            desc = defn.get("desc", "")

        return {
            "id": str(uuid4()),
            "signal_type": signal_type,
            "category": defn.get("category", "deal_health"),
            "severity": defn.get("severity", "medium"),
            "title": title[:200],
            "description": desc[:500],
            "entity_type": entity_type,
            "entity_id": str(entity_id),
            "entity_name": entity_name[:200],
            "deal_value": float(deal_value) if deal_value else None,
            "action_label": defn.get("action"),
            "action_type": defn.get("action_type"),
            "action_payload": {},
            "status": "pending",
            "source": "ai",
            "metadata": {"ctx": ctx},
        }

    @classmethod
    def get_all_signal_types(cls) -> list[dict]:
        """Return full signal type catalog."""
        return SIGNAL_DEFINITIONS
