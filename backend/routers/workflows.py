"""Workflow Builder API."""
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from supabase import Client
from dependencies import get_supabase, require_active_subscription
from models.schemas import WorkflowCreate, WorkflowUpdate, WorkflowOut, WorkflowRunOut
from services.workflow_engine import WorkflowEngine
from services.ai_service import ai_service
from services.email_service import email_service

router = APIRouter(prefix="/workflows", tags=["workflows"])


def _get_engine(supabase: Client) -> WorkflowEngine:
    return WorkflowEngine(supabase, ai_service, email_service)


@router.get("", response_model=list[WorkflowOut])
async def list_workflows(
    current_user: dict = Depends(require_active_subscription),
    supabase: Client = Depends(get_supabase),
):
    resp = (
        supabase.table("workflows")
        .select("*")
        .eq("user_id", current_user["id"])
        .order("updated_at", desc=True)
        .execute()
    )
    return resp.data or []


@router.post("", response_model=WorkflowOut, status_code=201)
async def create_workflow(
    body: WorkflowCreate,
    current_user: dict = Depends(require_active_subscription),
    supabase: Client = Depends(get_supabase),
):
    engine = _get_engine(supabase)

    # If template_id, use built-in template structure
    nodes = body.nodes
    edges = body.edges
    if body.template_id:
        template = engine.get_template(body.template_id)
        if template:
            nodes = template.get("nodes", nodes)
            edges = template.get("edges", edges)

    data = {
        "user_id": current_user["id"],
        "name": body.name,
        "description": body.description,
        "trigger_type": body.trigger_type,
        "trigger_config": body.trigger_config,
        "nodes": nodes,
        "edges": edges,
        "template_id": body.template_id,
        "status": "active",
    }
    resp = supabase.table("workflows").insert(data).execute()
    if not resp.data:
        raise HTTPException(status_code=500, detail="Failed to create workflow")
    return resp.data[0]


@router.get("/templates")
async def list_templates():
    """Return all built-in workflow templates."""
    engine = WorkflowEngine.__new__(WorkflowEngine)  # no-init
    return [
        {
            "id": k,
            "name": v["name"],
            "trigger_type": v["trigger_type"],
            "node_count": len(v.get("nodes", [])),
        }
        for k, v in WorkflowEngine.BUILTIN_TEMPLATES.items()
    ]


@router.get("/templates/{template_id}")
async def get_template(template_id: str):
    template = WorkflowEngine.BUILTIN_TEMPLATES.get(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template


@router.get("/{workflow_id}", response_model=WorkflowOut)
async def get_workflow(
    workflow_id: str,
    current_user: dict = Depends(require_active_subscription),
    supabase: Client = Depends(get_supabase),
):
    resp = (
        supabase.table("workflows")
        .select("*")
        .eq("id", workflow_id)
        .eq("user_id", current_user["id"])
        .single()
        .execute()
    )
    if not resp.data:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return resp.data


@router.patch("/{workflow_id}", response_model=WorkflowOut)
async def update_workflow(
    workflow_id: str,
    body: WorkflowUpdate,
    current_user: dict = Depends(require_active_subscription),
    supabase: Client = Depends(get_supabase),
):
    update = body.model_dump(exclude_none=True)
    if not update:
        raise HTTPException(status_code=400, detail="No fields to update")

    resp = (
        supabase.table("workflows")
        .update(update)
        .eq("id", workflow_id)
        .eq("user_id", current_user["id"])
        .execute()
    )
    if not resp.data:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return resp.data[0]


@router.delete("/{workflow_id}", status_code=204)
async def delete_workflow(
    workflow_id: str,
    current_user: dict = Depends(require_active_subscription),
    supabase: Client = Depends(get_supabase),
):
    supabase.table("workflows").delete().eq("id", workflow_id).eq("user_id", current_user["id"]).execute()


@router.post("/{workflow_id}/run")
async def run_workflow(
    workflow_id: str,
    current_user: dict = Depends(require_active_subscription),
    supabase: Client = Depends(get_supabase),
):
    """Manually trigger a workflow run."""
    resp = (
        supabase.table("workflows")
        .select("*")
        .eq("id", workflow_id)
        .eq("user_id", current_user["id"])
        .single()
        .execute()
    )
    if not resp.data:
        raise HTTPException(status_code=404, detail="Workflow not found")

    engine = _get_engine(supabase)
    result = await engine.execute_workflow(resp.data, {"manual": True, "user_id": current_user["id"]})
    return result


@router.get("/{workflow_id}/runs", response_model=list[WorkflowRunOut])
async def list_runs(
    workflow_id: str,
    limit: int = 20,
    current_user: dict = Depends(require_active_subscription),
    supabase: Client = Depends(get_supabase),
):
    resp = (
        supabase.table("workflow_runs")
        .select("*")
        .eq("workflow_id", workflow_id)
        .eq("user_id", current_user["id"])
        .order("started_at", desc=True)
        .limit(limit)
        .execute()
    )
    return resp.data or []
