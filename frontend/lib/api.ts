/**
 * Belon API client — typed wrapper around the FastAPI backend.
 * All requests include the Supabase session token.
 */
import { supabase } from "./supabase";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function getAuthHeaders(): Promise<Record<string, string>> {
  const { data } = await supabase.auth.getSession();
  const token = data.session?.access_token;
  return token
    ? { Authorization: `Bearer ${token}`, "Content-Type": "application/json" }
    : { "Content-Type": "application/json" };
}

async function request<T>(
  method: string,
  path: string,
  body?: unknown,
  extraHeaders?: Record<string, string>
): Promise<T> {
  const headers = { ...(await getAuthHeaders()), ...extraHeaders };
  const resp = await fetch(`${API_URL}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ detail: resp.statusText }));
    throw new Error(err.detail || `API error ${resp.status}`);
  }
  return resp.json() as Promise<T>;
}

// ── Types ──────────────────────────────────────────────────────────────────

export interface Signal {
  id: string;
  signal_type: string;
  category: string;
  severity: "critical" | "high" | "medium" | "low" | "info";
  title: string;
  description: string | null;
  entity_type: string | null;
  entity_name: string | null;
  deal_value: number | null;
  action_label: string | null;
  action_type: string | null;
  status: string;
  source: string;
  created_at: string;
}

export interface Workflow {
  id: string;
  name: string;
  description: string | null;
  status: string;
  trigger_type: string;
  nodes: unknown[];
  edges: unknown[];
  run_count: number;
  success_count: number;
  fail_count: number;
  last_run_at: string | null;
  template_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface WorkflowRun {
  id: string;
  workflow_id: string;
  status: string;
  nodes_executed: number;
  error_message: string | null;
  started_at: string;
  completed_at: string | null;
  duration_ms: number | null;
}

export interface ControlCenterStats {
  pipeline_health: number;
  active_deals: number;
  at_risk_revenue: number;
  signals_today: number;
  workflows_running: number;
  actions_completed_today: number;
  actions_total_today: number;
}

export interface AIActionResult {
  action_type: string;
  output: string;
  model_used: string;
  latency_ms: number;
  action_id?: string;
}

export interface Integration {
  id: string;
  provider: string;
  status: string;
  account_name: string | null;
  last_sync_at: string | null;
  records_synced: number;
}

// ── Signals ────────────────────────────────────────────────────────────────

export const signalsApi = {
  list: (params?: { status?: string; category?: string; severity?: string; limit?: number }) =>
    request<Signal[]>("GET", `/signals?${new URLSearchParams(params as Record<string, string> || {}).toString()}`),
  stats: () => request<{ total_pending: number; by_severity: Record<string, number>; by_category: Record<string, number> }>("GET", "/signals/stats"),
  action: (id: string, action: string) => request("POST", `/signals/${id}/action`, { action }),
  runEngine: () => request<{ signals_generated: number }>("POST", "/signals/run-engine"),
};

// ── Workflows ──────────────────────────────────────────────────────────────

export const workflowsApi = {
  list: () => request<Workflow[]>("GET", "/workflows"),
  create: (data: { name: string; trigger_type: string; template_id?: string; nodes?: unknown[]; edges?: unknown[] }) =>
    request<Workflow>("POST", "/workflows", data),
  update: (id: string, data: Partial<Workflow>) => request<Workflow>("PATCH", `/workflows/${id}`, data),
  delete: (id: string) => request("DELETE", `/workflows/${id}`),
  run: (id: string) => request<WorkflowRun>("POST", `/workflows/${id}/run`),
  runs: (id: string) => request<WorkflowRun[]>("GET", `/workflows/${id}/runs`),
  templates: () => request<{ id: string; name: string; trigger_type: string; node_count: number }[]>("GET", "/workflows/templates"),
  getTemplate: (id: string) => request("GET", `/workflows/templates/${id}`),
};

// ── Deals ──────────────────────────────────────────────────────────────────

export const dealsApi = {
  list: (stage?: string) => request("GET", `/deals${stage ? `?stage=${stage}` : ""}`),
  stats: () => request<ControlCenterStats>("GET", "/deals/stats"),
};

// ── AI ─────────────────────────────────────────────────────────────────────

export const aiApi = {
  runAction: (action_type: string, context: Record<string, unknown>, signal_id?: string) =>
    request<AIActionResult>("POST", "/ai/action", { action_type, context, signal_id }),
};

// ── Billing ────────────────────────────────────────────────────────────────

export const billingApi = {
  createCheckout: (success_url: string, cancel_url: string) =>
    request<{ checkout_url: string }>("POST", "/billing/checkout", { success_url, cancel_url }),
  portal: (return_url: string) =>
    request<{ portal_url: string }>("POST", `/billing/portal?return_url=${encodeURIComponent(return_url)}`),
  subscription: () => request("GET", "/billing/subscription"),
};

// ── Integrations ───────────────────────────────────────────────────────────

export const integrationsApi = {
  list: () => request<Integration[]>("GET", "/integrations"),
  hubspotConnect: () => request<{ auth_url: string }>("GET", "/integrations/hubspot/connect"),
  hubspotSync: (entity_types?: string[]) =>
    request("POST", "/integrations/hubspot/sync", { entity_types: entity_types || ["contacts", "deals"] }),
  disconnect: (provider: string) => request("DELETE", `/integrations/${provider}`),
  status: (provider: string) => request<Partial<Integration>>("GET", `/integrations/${provider}/status`),
};
