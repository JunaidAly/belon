"""Pydantic models for request/response validation."""
from __future__ import annotations
from datetime import datetime, date
from typing import Any, Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, ConfigDict


# ── Shared ────────────────────────────────────────────────────────────────────

class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=20, ge=1, le=100)


# ── Auth / Profile ─────────────────────────────────────────────────────────────

class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    company_name: Optional[str] = None
    timezone: Optional[str] = None


class ProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    email: str
    full_name: Optional[str] = None
    company_name: Optional[str] = None
    role: str
    onboarded: bool
    created_at: datetime


# ── Subscription ───────────────────────────────────────────────────────────────

class SubscriptionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    status: str
    trial_end: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    cancel_at_period_end: bool
    stripe_customer_id: Optional[str] = None


class CreateCheckoutSession(BaseModel):
    success_url: str
    cancel_url: str


# ── Signals ────────────────────────────────────────────────────────────────────

class SignalOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    signal_type: str
    category: str
    severity: str
    title: str
    description: Optional[str] = None
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    entity_name: Optional[str] = None
    deal_value: Optional[float] = None
    action_label: Optional[str] = None
    action_type: Optional[str] = None
    action_payload: dict = {}
    status: str
    source: str
    metadata: dict = {}
    actioned_at: Optional[datetime] = None
    created_at: datetime


class SignalAction(BaseModel):
    action: str = Field(..., description="actioned | dismissed | snoozed")
    snoozed_until: Optional[datetime] = None


class SignalFilter(BaseModel):
    category: Optional[str] = None
    severity: Optional[str] = None
    status: Optional[str] = "pending"
    entity_type: Optional[str] = None
    limit: int = Field(default=50, ge=1, le=200)
    offset: int = Field(default=0, ge=0)


# ── Workflows ─────────────────────────────────────────────────────────────────

class WorkflowNodeData(BaseModel):
    kind: str  # trigger | condition | ai | crm | notification
    label: str
    color: str
    config: dict = {}


class WorkflowNode(BaseModel):
    id: str
    type: str = "workflow"
    position: dict
    data: WorkflowNodeData


class WorkflowEdge(BaseModel):
    id: str
    source: str
    target: str
    sourceHandle: Optional[str] = None
    targetHandle: Optional[str] = None
    label: Optional[str] = None


class WorkflowCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    trigger_type: str
    trigger_config: dict = {}
    nodes: list[dict] = []
    edges: list[dict] = []
    template_id: Optional[str] = None


class WorkflowUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    trigger_config: Optional[dict] = None
    nodes: Optional[list[dict]] = None
    edges: Optional[list[dict]] = None


class WorkflowOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    description: Optional[str] = None
    status: str
    trigger_type: str
    trigger_config: dict = {}
    nodes: list = []
    edges: list = []
    run_count: int
    success_count: int
    fail_count: int
    last_run_at: Optional[datetime] = None
    template_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class WorkflowRunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    workflow_id: UUID
    status: str
    nodes_executed: int
    trigger_data: dict = {}
    result: dict = {}
    error_message: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None


# ── Integrations ──────────────────────────────────────────────────────────────

class IntegrationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    provider: str
    status: str
    account_id: Optional[str] = None
    account_name: Optional[str] = None
    last_sync_at: Optional[datetime] = None
    records_synced: int
    sync_error: Optional[str] = None
    created_at: datetime


class HubSpotAuthCallback(BaseModel):
    code: str
    state: Optional[str] = None


class TriggerSyncRequest(BaseModel):
    entity_types: list[str] = ["contacts", "deals", "companies"]
    full_sync: bool = False


# ── Deals ─────────────────────────────────────────────────────────────────────

class DealOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    company_name: Optional[str] = None
    contact_name: Optional[str] = None
    value: float
    stage: str
    health_score: int
    owner_name: Optional[str] = None
    days_in_stage: int
    last_activity_at: Optional[datetime] = None
    expected_close_date: Optional[date] = None
    probability: int
    source: str
    created_at: datetime


# ── AI ────────────────────────────────────────────────────────────────────────

class AIRequest(BaseModel):
    action_type: str = Field(..., description="email_draft | lead_score | deal_analysis | sequence_generate | churn_prediction")
    context: dict = Field(default={}, description="Context data for the AI action")
    signal_id: Optional[str] = None
    model: Optional[str] = None  # override default model


class AIResponse(BaseModel):
    action_type: str
    output: str
    model_used: str
    tokens_used: Optional[int] = None
    latency_ms: int
    action_id: Optional[str] = None


# ── Stripe Webhook ────────────────────────────────────────────────────────────

class StripeWebhookEvent(BaseModel):
    id: str
    type: str
    data: dict


# ── Dashboard Stats ───────────────────────────────────────────────────────────

class ControlCenterStats(BaseModel):
    pipeline_health: int
    active_deals: int
    at_risk_revenue: float
    signals_today: int
    workflows_running: int
    actions_completed_today: int
    actions_total_today: int
