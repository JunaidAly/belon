"use client";
import { useEffect, useState, useCallback } from "react";
import {
  Clock, AlertTriangle, DollarSign, TrendingDown, Mail,
  ArrowRight, CheckCircle2, Zap, Activity, RefreshCw,
} from "lucide-react";
import { toast } from "sonner";
import { signalsApi, dealsApi, type Signal, type ControlCenterStats } from "@/lib/api";
import { formatCurrency, formatTimeAgo, SEVERITY_COLORS } from "@/lib/utils";

const ICON_MAP: Record<string, React.ElementType> = {
  critical: AlertTriangle,
  high: TrendingDown,
  medium: Clock,
  low: CheckCircle2,
  info: Activity,
};

function StatCard({ label, value, sub, accent = false }: { label: string; value: string; sub?: string; accent?: boolean }) {
  return (
    <div className="belon-enter-up rounded-2xl border border-white/10 bg-white/5 p-4 backdrop-blur-sm sm:p-5">
      <div className="mb-1 text-sm text-white/50">{label}</div>
      <div className={`mb-1 text-2xl font-medium ${accent ? "text-[#f97316]" : ""}`}>{value}</div>
      {sub && <div className="text-xs text-white/40">{sub}</div>}
    </div>
  );
}

function SignalActionCard({ signal, onAction }: { signal: Signal; onAction: (id: string) => void }) {
  const Icon = ICON_MAP[signal.severity] || Clock;
  const colors = SEVERITY_COLORS[signal.severity as keyof typeof SEVERITY_COLORS];
  const isPulsing = signal.severity === "critical";

  return (
    <div
      className={`belon-enter-x group rounded-2xl border bg-white/5 p-4 backdrop-blur-sm transition-colors hover:bg-white/[0.07] sm:p-5 ${
        isPulsing ? "border-red-500/30" : colors.border
      }`}
    >
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:gap-5">
        <div className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-xl ${colors.bg} ${colors.text}`}>
          <Icon className="h-5 w-5" strokeWidth={2} />
        </div>

        <div className="min-w-0 flex-1">
          <div className="mb-1 flex items-start gap-2">
            <h3 className="flex-1 text-base font-medium leading-snug">{signal.title}</h3>
            {signal.severity === "critical" && (
              <span className="shrink-0 rounded-full border border-red-500/20 bg-red-500/10 px-2 py-0.5 text-xs text-red-400">
                Critical
              </span>
            )}
          </div>
          {signal.description && (
            <p className="mb-3 text-sm leading-relaxed text-white/55">{signal.description}</p>
          )}
          <div className="flex flex-wrap items-center gap-2">
            {signal.action_label && (
              <button
                type="button"
                onClick={() => onAction(signal.id)}
                className="inline-flex min-h-10 items-center gap-2 rounded-xl border border-white/10 bg-white/10 px-4 py-2 text-sm transition-colors hover:bg-white/15"
              >
                <span>{signal.action_label}</span>
                <ArrowRight className="h-3.5 w-3.5" />
              </button>
            )}
            {signal.deal_value && (
              <span className="text-xs text-white/40">{formatCurrency(signal.deal_value)}</span>
            )}
            <span className="text-xs text-white/30">{formatTimeAgo(signal.created_at)}</span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function ControlCenterPage() {
  const [signals, setSignals] = useState<Signal[]>([]);
  const [stats, setStats] = useState<ControlCenterStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const loadData = useCallback(async () => {
    try {
      const [sigs, st] = await Promise.all([
        signalsApi.list({ status: "pending", limit: 20 }),
        dealsApi.stats(),
      ]);
      setSignals(sigs);
      setStats(st);
    } catch (err) {
      // Show mock data if API not yet running
      setSignals(MOCK_SIGNALS);
      setStats(MOCK_STATS);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadData(); }, [loadData]);

  // Supabase Realtime — live signal updates
  useEffect(() => {
    const { supabase } = require("@/lib/supabase");
    const channel = supabase
      .channel("signals-feed")
      .on("postgres_changes", { event: "INSERT", schema: "public", table: "signals" }, (payload: { new: Signal }) => {
        setSignals((prev) => [payload.new, ...prev.slice(0, 19)]);
        toast.info(`New signal: ${payload.new.title}`, { duration: 4000 });
      })
      .subscribe();
    return () => { supabase.removeChannel(channel); };
  }, []);

  const handleAction = async (signalId: string) => {
    const signal = signals.find((s) => s.id === signalId);
    try {
      await signalsApi.action(signalId, "actioned");
      setSignals((prev) => prev.filter((s) => s.id !== signalId));
      toast.success("Action queued", { description: signal?.action_label });
    } catch {
      toast.error("Failed to queue action");
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      await signalsApi.runEngine();
      await loadData();
      toast.success("Signal engine refreshed");
    } catch {
      await loadData();
    } finally {
      setRefreshing(false);
    }
  };

  const criticalCount = signals.filter((s) => s.severity === "critical").length;

  return (
    <div className="mx-auto w-full max-w-7xl px-4 py-6 sm:p-6 lg:p-8">
      {/* Header */}
      <div className="belon-enter-up mb-6 flex items-start justify-between gap-4 sm:mb-8">
        <div>
          <h1 className="mb-1 text-2xl font-medium leading-snug sm:text-3xl">
            Automation Control Center
          </h1>
          <p className="text-base text-white/55">
            {loading ? "Loading signals…" : criticalCount > 0 ? (
              <>AI found <span className="font-medium text-red-400">{criticalCount} critical issue{criticalCount > 1 ? "s" : ""}</span> in your pipeline</>
            ) : (
              <>Pipeline looks healthy · {signals.length} pending signal{signals.length !== 1 ? "s" : ""}</>
            )}
          </p>
        </div>
        <button
          onClick={handleRefresh}
          disabled={refreshing}
          className="flex shrink-0 items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm transition-colors hover:bg-white/10 disabled:opacity-50"
        >
          <RefreshCw className={`h-4 w-4 ${refreshing ? "animate-spin" : ""}`} />
          <span className="hidden sm:inline">Refresh</span>
        </button>
      </div>

      {/* Stats */}
      {stats && (
        <div className="mb-6 grid grid-cols-2 gap-3 sm:mb-8 sm:grid-cols-4 sm:gap-4">
          <StatCard label="Pipeline Health" value={`${stats.pipeline_health}%`} sub={stats.pipeline_health < 50 ? "⚠ At risk" : "✓ On track"} accent={stats.pipeline_health < 50} />
          <StatCard label="Active Deals" value={String(stats.active_deals)} />
          <StatCard label="At-Risk Revenue" value={formatCurrency(stats.at_risk_revenue)} accent={stats.at_risk_revenue > 0} />
          <StatCard label="Signals Today" value={String(stats.signals_today)} sub={`${stats.workflows_running} workflows live`} />
        </div>
      )}

      {/* Live indicator */}
      <div className="mb-4 flex items-center gap-2">
        <div className="belon-live-dot h-2 w-2 rounded-full bg-[#f97316]" />
        <span className="text-sm text-white/50">Live — Agent scanning pipeline every 15 min</span>
      </div>

      {/* Signal feed */}
      {loading ? (
        <div className="space-y-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-28 animate-pulse rounded-2xl border border-white/10 bg-white/5" />
          ))}
        </div>
      ) : signals.length === 0 ? (
        <div className="rounded-2xl border border-white/10 bg-white/5 p-12 text-center">
          <CheckCircle2 className="mx-auto mb-3 h-10 w-10 text-emerald-500" />
          <p className="font-medium">All clear — no pending signals</p>
          <p className="mt-1 text-sm text-white/50">Agent is monitoring. New signals will appear here in real time.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {signals.map((signal, i) => (
            <div key={signal.id} style={{ animationDelay: `${i * 40}ms` }}>
              <SignalActionCard signal={signal} onAction={handleAction} />
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ── Mock data (shown when backend not yet running) ─────────────────────────

const MOCK_STATS: ControlCenterStats = {
  pipeline_health: 72, active_deals: 47, at_risk_revenue: 1_240_000,
  signals_today: 6, workflows_running: 4, actions_completed_today: 18, actions_total_today: 24,
};

const MOCK_SIGNALS: Signal[] = [
  { id: "1", signal_type: "deal_stalled_14d", category: "deal_health", severity: "critical", title: "TechFlow Inc deal stalled for 14 days", description: "No contact activity logged since Feb 28. Last email unopened. Deal value: $125K.", entity_type: "deal", entity_name: "TechFlow Inc", deal_value: 125000, action_label: "Draft re-engagement email", action_type: "ai_draft", status: "pending", source: "ai", created_at: new Date(Date.now() - 3600000).toISOString() },
  { id: "2", signal_type: "deal_no_next_step", category: "deal_health", severity: "high", title: "3 high-value deals missing next steps", description: "Combined value of $380K. No follow-up tasks created after last touchpoint.", entity_type: "pipeline", entity_name: "Pipeline", deal_value: 380000, action_label: "Generate task sequences", action_type: "workflow", status: "pending", source: "ai", created_at: new Date(Date.now() - 7200000).toISOString() },
  { id: "3", signal_type: "pricing_page_visit", category: "buying_signal", severity: "high", title: "Acme Corp showing buying signals", description: "Pricing page visited 12 times this week. 3 stakeholders engaged on LinkedIn.", entity_type: "deal", entity_name: "Acme Corp", deal_value: 165000, action_label: "Schedule discovery call", action_type: "schedule", status: "pending", source: "ai", created_at: new Date(Date.now() - 10800000).toISOString() },
  { id: "4", signal_type: "renewal_critical", category: "churn_risk", severity: "critical", title: "DataSync renewal at risk", description: "Contract expires in 12 days. Champion left company 3 weeks ago. $95K ARR.", entity_type: "deal", entity_name: "DataSync Corp", deal_value: 95000, action_label: "Identify new champion", action_type: "workflow", status: "pending", source: "ai", created_at: new Date(Date.now() - 14400000).toISOString() },
  { id: "5", signal_type: "rep_no_followups", category: "rep_performance", severity: "medium", title: "Sarah hasn't followed up with GlobalTech", description: "Meeting was 5 days ago. Strong interest indicated but no next steps logged.", entity_type: "rep", entity_name: "Sarah Johnson", deal_value: 340000, action_label: "Send follow-up reminder", action_type: "email", status: "pending", source: "ai", created_at: new Date(Date.now() - 18000000).toISOString() },
];
