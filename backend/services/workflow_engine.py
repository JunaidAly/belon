"""
Belon Workflow Engine — 6 core automation workflows.
Executes node graphs stored in the workflows table.
"""
from __future__ import annotations
import asyncio
import logging
import time
from datetime import datetime
from uuid import uuid4
from typing import Any

logger = logging.getLogger(__name__)


# ── Node Executor ─────────────────────────────────────────────────────────────

class NodeExecutor:
    """Executes a single workflow node based on its kind."""

    def __init__(self, supabase, ai_service, email_service):
        self.supabase = supabase
        self.ai_service = ai_service
        self.email_service = email_service

    async def execute(self, node: dict, context: dict) -> dict:
        kind = node.get("data", {}).get("kind", "")
        config = node.get("data", {}).get("config", {})
        label = node.get("data", {}).get("label", "")

        handler = {
            "trigger": self._handle_trigger,
            "condition": self._handle_condition,
            "ai": self._handle_ai,
            "crm": self._handle_crm,
            "notification": self._handle_notification,
        }.get(kind, self._handle_unknown)

        return await handler(node, config, context, label)

    async def _handle_trigger(self, node, config, context, label) -> dict:
        return {"status": "ok", "output": "Trigger evaluated", "passed": True}

    async def _handle_condition(self, node, config, context, label) -> dict:
        """Evaluate condition against context."""
        field = config.get("field", "health_score")
        operator = config.get("operator", "lt")
        value = config.get("value", 50)

        actual = context.get(field, 0)
        passed = False
        if operator == "lt":
            passed = float(actual) < float(value)
        elif operator == "gt":
            passed = float(actual) > float(value)
        elif operator == "eq":
            passed = str(actual) == str(value)
        elif operator == "gte":
            passed = float(actual) >= float(value)
        elif operator == "lte":
            passed = float(actual) <= float(value)
        elif operator == "contains":
            passed = str(value).lower() in str(actual).lower()

        return {"status": "ok", "output": f"Condition '{label}': {passed}", "passed": passed}

    async def _handle_ai(self, node, config, context, label) -> dict:
        """Run AI action."""
        action_type = config.get("action_type", "deal_analysis")
        try:
            result = await self.ai_service.run_action(action_type, context)
            return {
                "status": "ok",
                "output": result.get("output", ""),
                "model_used": result.get("model_used"),
                "latency_ms": result.get("latency_ms"),
            }
        except Exception as e:
            logger.error(f"AI node failed: {e}")
            return {"status": "error", "output": str(e), "error": True}

    async def _handle_crm(self, node, config, context, label) -> dict:
        """Update CRM record via Supabase."""
        entity_type = config.get("entity_type", "deals")
        entity_id = context.get("deal_id") or context.get("entity_id")
        updates = config.get("updates", {})

        if entity_id and updates:
            try:
                self.supabase.table(entity_type).update(updates).eq("id", entity_id).execute()
                return {"status": "ok", "output": f"Updated {entity_type}/{entity_id}"}
            except Exception as e:
                logger.error(f"CRM update failed: {e}")
                return {"status": "error", "output": str(e), "error": True}

        return {"status": "ok", "output": "CRM action skipped — no entity_id"}

    async def _handle_notification(self, node, config, context, label) -> dict:
        """Send notification email or Slack message."""
        channel = config.get("channel", "email")
        recipient = config.get("recipient") or context.get("owner_email") or context.get("user_email")
        message = config.get("message", label)

        if channel == "email" and recipient:
            try:
                await self.email_service.send_notification(
                    to=recipient,
                    subject=f"Belon Alert: {context.get('company_name', 'Deal')}",
                    body=message,
                    context=context,
                )
                return {"status": "ok", "output": f"Email sent to {recipient}"}
            except Exception as e:
                logger.error(f"Notification failed: {e}")
                return {"status": "error", "output": str(e), "error": True}

        return {"status": "ok", "output": f"Notification queued ({channel})"}

    async def _handle_unknown(self, node, config, context, label) -> dict:
        return {"status": "ok", "output": f"Node '{label}' processed"}


# ── Workflow Runner ───────────────────────────────────────────────────────────

class WorkflowEngine:
    """
    Executes workflow node graphs.
    Supports: Stalled Deal Recovery, Lead Qualification, Churn Risk Alert,
              Deal Velocity, Buying Signal Outreach, Pipeline Health Check.
    """

    BUILTIN_TEMPLATES = {
        "stalled-deal-recovery": {
            "name": "Stalled Deal Recovery",
            "trigger_type": "signal_fired",
            "nodes": [
                {"id": "1", "type": "workflow", "position": {"x": 80, "y": 160}, "data": {"kind": "trigger", "label": "Signal: Deal Stalled 14d", "color": "#3b82f6", "config": {"signal_type": "deal_stalled_14d"}}},
                {"id": "2", "type": "workflow", "position": {"x": 300, "y": 160}, "data": {"kind": "condition", "label": "Deal Value > $50K?", "color": "#f59e0b", "config": {"field": "value", "operator": "gt", "value": 50000}}},
                {"id": "3", "type": "workflow", "position": {"x": 520, "y": 100}, "data": {"kind": "ai", "label": "Analyze Deal Health", "color": "#7c3aed", "config": {"action_type": "deal_analysis"}}},
                {"id": "4", "type": "workflow", "position": {"x": 740, "y": 100}, "data": {"kind": "ai", "label": "Generate Re-Engagement Email", "color": "#7c3aed", "config": {"action_type": "email_draft"}}},
                {"id": "5", "type": "workflow", "position": {"x": 520, "y": 240}, "data": {"kind": "crm", "label": "Update Deal Notes", "color": "#10b981", "config": {"entity_type": "deals", "updates": {"health_score": 35}}}},
                {"id": "6", "type": "workflow", "position": {"x": 960, "y": 160}, "data": {"kind": "notification", "label": "Alert Deal Owner", "color": "#f97316", "config": {"channel": "email"}}},
            ],
            "edges": [
                {"id": "e1-2", "source": "1", "target": "2"},
                {"id": "e2-3", "source": "2", "target": "3", "label": "Yes"},
                {"id": "e2-5", "source": "2", "target": "5", "label": "No"},
                {"id": "e3-4", "source": "3", "target": "4"},
                {"id": "e4-6", "source": "4", "target": "6"},
                {"id": "e5-6", "source": "5", "target": "6"},
            ],
        },
        "lead-qualification": {
            "name": "Instant Lead Qualification",
            "trigger_type": "contact_created",
            "nodes": [
                {"id": "1", "type": "workflow", "position": {"x": 80, "y": 160}, "data": {"kind": "trigger", "label": "New Contact Created", "color": "#3b82f6", "config": {}}},
                {"id": "2", "type": "workflow", "position": {"x": 300, "y": 160}, "data": {"kind": "ai", "label": "Score Lead (AI)", "color": "#7c3aed", "config": {"action_type": "lead_score"}}},
                {"id": "3", "type": "workflow", "position": {"x": 520, "y": 160}, "data": {"kind": "condition", "label": "Score >= 70?", "color": "#f59e0b", "config": {"field": "lead_score", "operator": "gte", "value": 70}}},
                {"id": "4", "type": "workflow", "position": {"x": 740, "y": 80}, "data": {"kind": "crm", "label": "Tag: Hot Lead", "color": "#10b981", "config": {"entity_type": "contacts", "updates": {"status": "prospect"}}}},
                {"id": "5", "type": "workflow", "position": {"x": 740, "y": 240}, "data": {"kind": "crm", "label": "Tag: Nurture", "color": "#10b981", "config": {"entity_type": "contacts", "updates": {"status": "lead"}}}},
                {"id": "6", "type": "workflow", "position": {"x": 960, "y": 160}, "data": {"kind": "notification", "label": "Notify Sales Rep", "color": "#f97316", "config": {"channel": "email"}}},
            ],
            "edges": [
                {"id": "e1-2", "source": "1", "target": "2"},
                {"id": "e2-3", "source": "2", "target": "3"},
                {"id": "e3-4", "source": "3", "target": "4", "label": "Yes"},
                {"id": "e3-5", "source": "3", "target": "5", "label": "No"},
                {"id": "e4-6", "source": "4", "target": "6"},
            ],
        },
        "churn-risk-alert": {
            "name": "Churn Risk Alert",
            "trigger_type": "signal_fired",
            "nodes": [
                {"id": "1", "type": "workflow", "position": {"x": 80, "y": 160}, "data": {"kind": "trigger", "label": "Signal: Churn Risk", "color": "#3b82f6", "config": {"signal_type": "renewal_critical"}}},
                {"id": "2", "type": "workflow", "position": {"x": 300, "y": 160}, "data": {"kind": "ai", "label": "Churn Risk Analysis", "color": "#7c3aed", "config": {"action_type": "churn_prediction"}}},
                {"id": "3", "type": "workflow", "position": {"x": 520, "y": 160}, "data": {"kind": "ai", "label": "Generate Save Email", "color": "#7c3aed", "config": {"action_type": "re_engagement"}}},
                {"id": "4", "type": "workflow", "position": {"x": 740, "y": 160}, "data": {"kind": "crm", "label": "Flag: At Risk", "color": "#10b981", "config": {"entity_type": "deals", "updates": {"health_score": 20}}}},
                {"id": "5", "type": "workflow", "position": {"x": 960, "y": 160}, "data": {"kind": "notification", "label": "Urgent Alert to CS", "color": "#f97316", "config": {"channel": "email"}}},
            ],
            "edges": [
                {"id": "e1-2", "source": "1", "target": "2"},
                {"id": "e2-3", "source": "2", "target": "3"},
                {"id": "e3-4", "source": "3", "target": "4"},
                {"id": "e4-5", "source": "4", "target": "5"},
            ],
        },
        "buying-signal-outreach": {
            "name": "Buying Signal Fast-Track",
            "trigger_type": "signal_fired",
            "nodes": [
                {"id": "1", "type": "workflow", "position": {"x": 80, "y": 160}, "data": {"kind": "trigger", "label": "Signal: Buying Intent", "color": "#3b82f6", "config": {"signal_category": "buying_signal"}}},
                {"id": "2", "type": "workflow", "position": {"x": 300, "y": 160}, "data": {"kind": "ai", "label": "Enrich Company", "color": "#7c3aed", "config": {"action_type": "enrichment"}}},
                {"id": "3", "type": "workflow", "position": {"x": 520, "y": 160}, "data": {"kind": "ai", "label": "Personalized Outreach", "color": "#7c3aed", "config": {"action_type": "email_draft"}}},
                {"id": "4", "type": "workflow", "position": {"x": 740, "y": 160}, "data": {"kind": "crm", "label": "Create Deal", "color": "#10b981", "config": {"entity_type": "deals", "updates": {"stage": "qualification"}}}},
                {"id": "5", "type": "workflow", "position": {"x": 960, "y": 160}, "data": {"kind": "notification", "label": "Alert: Hot Lead", "color": "#f97316", "config": {"channel": "email"}}},
            ],
            "edges": [
                {"id": "e1-2", "source": "1", "target": "2"},
                {"id": "e2-3", "source": "2", "target": "3"},
                {"id": "e3-4", "source": "3", "target": "4"},
                {"id": "e4-5", "source": "4", "target": "5"},
            ],
        },
        "deal-velocity": {
            "name": "Deal Velocity Optimizer",
            "trigger_type": "schedule",
            "nodes": [
                {"id": "1", "type": "workflow", "position": {"x": 80, "y": 160}, "data": {"kind": "trigger", "label": "Daily Schedule", "color": "#3b82f6", "config": {"cron": "0 9 * * *"}}},
                {"id": "2", "type": "workflow", "position": {"x": 300, "y": 160}, "data": {"kind": "condition", "label": "Days in Stage > 10?", "color": "#f59e0b", "config": {"field": "days_in_stage", "operator": "gt", "value": 10}}},
                {"id": "3", "type": "workflow", "position": {"x": 520, "y": 100}, "data": {"kind": "ai", "label": "Stage Advancement Plan", "color": "#7c3aed", "config": {"action_type": "deal_analysis"}}},
                {"id": "4", "type": "workflow", "position": {"x": 740, "y": 100}, "data": {"kind": "crm", "label": "Flag Stalled Deal", "color": "#10b981", "config": {"entity_type": "deals", "updates": {}}}},
                {"id": "5", "type": "workflow", "position": {"x": 520, "y": 240}, "data": {"kind": "notification", "label": "Rep Daily Digest", "color": "#f97316", "config": {"channel": "email"}}},
            ],
            "edges": [
                {"id": "e1-2", "source": "1", "target": "2"},
                {"id": "e2-3", "source": "2", "target": "3", "label": "Yes"},
                {"id": "e2-5", "source": "2", "target": "5", "label": "No"},
                {"id": "e3-4", "source": "3", "target": "4"},
                {"id": "e4-5", "source": "4", "target": "5"},
            ],
        },
        "pipeline-health-check": {
            "name": "Daily Pipeline Health Check",
            "trigger_type": "schedule",
            "nodes": [
                {"id": "1", "type": "workflow", "position": {"x": 80, "y": 160}, "data": {"kind": "trigger", "label": "Nightly Schedule", "color": "#3b82f6", "config": {"cron": "0 22 * * *"}}},
                {"id": "2", "type": "workflow", "position": {"x": 300, "y": 160}, "data": {"kind": "ai", "label": "Pipeline Forecast", "color": "#7c3aed", "config": {"action_type": "pipeline_forecast"}}},
                {"id": "3", "type": "workflow", "position": {"x": 520, "y": 160}, "data": {"kind": "condition", "label": "Critical Issues?", "color": "#f59e0b", "config": {"field": "critical_count", "operator": "gt", "value": 0}}},
                {"id": "4", "type": "workflow", "position": {"x": 740, "y": 100}, "data": {"kind": "notification", "label": "Critical Alert", "color": "#f97316", "config": {"channel": "email"}}},
                {"id": "5", "type": "workflow", "position": {"x": 740, "y": 240}, "data": {"kind": "notification", "label": "Daily Summary", "color": "#f97316", "config": {"channel": "email"}}},
            ],
            "edges": [
                {"id": "e1-2", "source": "1", "target": "2"},
                {"id": "e2-3", "source": "2", "target": "3"},
                {"id": "e3-4", "source": "3", "target": "4", "label": "Yes"},
                {"id": "e3-5", "source": "3", "target": "5", "label": "No"},
            ],
        },
    }

    def __init__(self, supabase, ai_service, email_service):
        self.supabase = supabase
        self.node_executor = NodeExecutor(supabase, ai_service, email_service)

    async def execute_workflow(self, workflow: dict, trigger_data: dict) -> dict:
        """Execute a workflow and record the run."""
        run_id = str(uuid4())
        workflow_id = workflow["id"]
        user_id = workflow["user_id"]
        nodes = workflow.get("nodes", [])
        edges = workflow.get("edges", [])

        # Create run record
        run_record = {
            "id": run_id,
            "workflow_id": workflow_id,
            "user_id": user_id,
            "status": "running",
            "trigger_data": trigger_data,
            "started_at": datetime.utcnow().isoformat(),
        }
        self.supabase.table("workflow_runs").insert(run_record).execute()

        start_time = time.time()
        context = {**trigger_data}
        node_results: dict[str, dict] = {}
        nodes_executed = 0
        error_message = None

        try:
            # Build adjacency map
            adj: dict[str, list[str]] = {}
            for edge in edges:
                src = edge.get("source")
                tgt = edge.get("target")
                if src and tgt:
                    adj.setdefault(src, []).append(tgt)

            # Find trigger nodes (entry points)
            node_map = {n["id"]: n for n in nodes}
            target_ids = {e.get("target") for e in edges}
            entry_nodes = [n for n in nodes if n["id"] not in target_ids]

            # BFS execution
            queue = list(entry_nodes)
            visited = set()

            while queue:
                node = queue.pop(0)
                node_id = node["id"]
                if node_id in visited:
                    continue
                visited.add(node_id)

                result = await self.node_executor.execute(node, context)
                node_results[node_id] = result
                nodes_executed += 1

                # Merge output into context
                if isinstance(result.get("output"), str):
                    context[f"node_{node_id}_output"] = result["output"]

                # Follow edges based on condition result
                for next_id in adj.get(node_id, []):
                    if next_id in node_map and next_id not in visited:
                        next_node = node_map[next_id]
                        # Check condition branching
                        edge_label = next((e.get("label", "") for e in edges
                                          if e.get("source") == node_id and e.get("target") == next_id), "")
                        if edge_label in ("No", "no") and result.get("passed", True):
                            continue  # Skip "No" branch if condition passed
                        if edge_label in ("Yes", "yes") and not result.get("passed", True):
                            continue  # Skip "Yes" branch if condition failed
                        queue.append(next_node)

            status = "completed"

        except Exception as e:
            logger.error(f"Workflow {workflow_id} execution failed: {e}")
            error_message = str(e)
            status = "failed"

        duration_ms = int((time.time() - start_time) * 1000)

        # Update run record
        self.supabase.table("workflow_runs").update({
            "status": status,
            "result": node_results,
            "nodes_executed": nodes_executed,
            "error_message": error_message,
            "completed_at": datetime.utcnow().isoformat(),
            "duration_ms": duration_ms,
        }).eq("id", run_id).execute()

        # Update workflow stats
        update_fields = {
            "run_count": workflow.get("run_count", 0) + 1,
            "last_run_at": datetime.utcnow().isoformat(),
        }
        if status == "completed":
            update_fields["success_count"] = workflow.get("success_count", 0) + 1
        else:
            update_fields["fail_count"] = workflow.get("fail_count", 0) + 1
        self.supabase.table("workflows").update(update_fields).eq("id", workflow_id).execute()

        return {
            "run_id": run_id,
            "status": status,
            "nodes_executed": nodes_executed,
            "duration_ms": duration_ms,
            "error": error_message,
        }

    async def run_scheduled_workflows(self, user_id: str) -> int:
        """Execute all active scheduled workflows for a user."""
        now = datetime.utcnow()
        workflows_resp = (
            self.supabase.table("workflows")
            .select("*")
            .eq("user_id", user_id)
            .eq("status", "active")
            .eq("trigger_type", "schedule")
            .execute()
        )
        workflows = workflows_resp.data or []
        count = 0
        for wf in workflows:
            next_run = wf.get("next_run_at")
            if next_run:
                try:
                    next_dt = datetime.fromisoformat(next_run.replace("Z", "+00:00")).replace(tzinfo=None)
                    if next_dt > now:
                        continue
                except (ValueError, AttributeError):
                    pass
            await self.execute_workflow(wf, {"scheduled": True, "run_at": now.isoformat()})
            count += 1
        return count

    def get_template(self, template_id: str) -> dict | None:
        return self.BUILTIN_TEMPLATES.get(template_id)
