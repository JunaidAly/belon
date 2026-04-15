"use client";
import { useEffect, useState, useCallback } from "react";
import { Filter, Zap, ArrowRight, RefreshCw } from "lucide-react";
import { toast } from "sonner";
import { signalsApi, type Signal } from "@/lib/api";
import { formatCurrency, formatTimeAgo, SEVERITY_COLORS, CATEGORY_LABELS } from "@/lib/utils";

const CATEGORIES = ["all", "deal_health", "buying_signal", "churn_risk", "rep_performance", "pipeline_health", "engagement", "ai_insight"];
const SEVERITIES = ["all", "critical", "high", "medium", "low", "info"];

const CATEGORY_ICONS: Record<string, string> = {
  deal_health: "🏥", buying_signal: "⚡", churn_risk: "🚨",
  rep_performance: "👤", pipeline_health: "📊", engagement: "💬", ai_insight: "🤖",
};

export default function SignalsPage() {
  const [signals, setSignals] = useState<Signal[]>([]);
  const [stats, setStats] = useState<{ total_pending: number; by_severity: Record<string, number>; by_category: Record<string, number> } | null>(null);
  const [loading, setLoading] = useState(true);
  const [category, setCategory] = useState("all");
  const [severity, setSeverity] = useState("all");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [sigs, st] = await Promise.all([
        signalsApi.list({
          status: "pending",
          category: category === "all" ? undefined : category,
          severity: severity === "all" ? undefined : severity,
          limit: 100,
        }),
        signalsApi.stats(),
      ]);
      setSignals(sigs);
      setStats(st);
    } catch {
      setSignals(MOCK_SIGNALS);
      setStats({ total_pending: MOCK_SIGNALS.length, by_severity: { critical: 2, high: 2, medium: 1 }, by_category: { deal_health: 2, buying_signal: 1, churn_risk: 1, rep_performance: 1 } });
    } finally {
      setLoading(false);
    }
  }, [category, severity]);

  useEffect(() => { load(); }, [load]);

  const handleAction = async (signal: Signal, action: "actioned" | "dismissed") => {
    try {
      await signalsApi.action(signal.id, action);
      setSignals((prev) => prev.filter((s) => s.id !== signal.id));
      toast.success(action === "actioned" ? `Queued: ${signal.action_label}` : "Signal dismissed");
    } catch {
      toast.error("Failed");
    }
  };

  return (
    <div className="flex h-full min-h-0 flex-col">
      {/* Stats bar */}
      {stats && (
        <div className="shrink-0 border-b border-white/5 bg-[#0d0e1a]/50 px-4 py-4 backdrop-blur-xl sm:px-6 lg:px-8">
          <div className="flex flex-wrap items-center gap-4">
            <div>
              <div className="text-2xl font-medium">{stats.total_pending}</div>
              <div className="text-xs text-white/50">Pending signals</div>
            </div>
            <div className="h-8 w-px bg-white/10" />
            {Object.entries(stats.by_severity).sort(([a], [b]) => ["critical","high","medium","low","info"].indexOf(a) - ["critical","high","medium","low","info"].indexOf(b)).map(([sev, count]) => {
              const colors = SEVERITY_COLORS[sev as keyof typeof SEVERITY_COLORS];
              return (
                <div key={sev} className="flex items-center gap-1.5">
                  <span className={`inline-flex h-5 min-w-5 items-center justify-center rounded-full px-1.5 text-xs ${colors.bg} ${colors.text}`}>{count}</span>
                  <span className="text-xs capitalize text-white/50">{sev}</span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="shrink-0 border-b border-white/5 bg-[#0d0e1a]/30 px-4 py-3 sm:px-6 lg:px-8">
        <div className="flex flex-wrap items-center gap-2">
          <Filter className="h-4 w-4 shrink-0 text-white/40" />
          <div className="flex flex-wrap gap-1.5">
            {CATEGORIES.map((cat) => (
              <button
                key={cat}
                onClick={() => setCategory(cat)}
                className={`rounded-lg px-2.5 py-1 text-xs transition-colors ${
                  category === cat
                    ? "bg-[#f97316] text-black font-medium"
                    : "border border-white/10 bg-white/5 text-white/60 hover:bg-white/10"
                }`}
              >
                {cat === "all" ? "All" : (CATEGORY_ICONS[cat] || "") + " " + (CATEGORY_LABELS[cat] || cat)}
              </button>
            ))}
          </div>
          <div className="h-5 w-px bg-white/10" />
          <div className="flex flex-wrap gap-1.5">
            {SEVERITIES.slice(0, 4).map((sev) => (
              <button
                key={sev}
                onClick={() => setSeverity(sev)}
                className={`rounded-lg px-2.5 py-1 text-xs capitalize transition-colors ${
                  severity === sev
                    ? "bg-white/20 text-white"
                    : "border border-white/10 bg-white/5 text-white/50 hover:bg-white/10"
                }`}
              >
                {sev}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Signal cards */}
      <div className="belon-scroll flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8">
        {loading ? (
          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="h-44 animate-pulse rounded-2xl border border-white/10 bg-white/5" />
            ))}
          </div>
        ) : signals.length === 0 ? (
          <div className="py-20 text-center">
            <Zap className="mx-auto mb-3 h-10 w-10 text-white/20" />
            <p className="text-white/50">No signals match your filters</p>
          </div>
        ) : (
          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
            {signals.map((signal, i) => {
              const colors = SEVERITY_COLORS[signal.severity as keyof typeof SEVERITY_COLORS];
              return (
                <div
                  key={signal.id}
                  style={{ animationDelay: `${i * 25}ms` }}
                  className={`belon-enter-up flex flex-col rounded-2xl border bg-white/5 p-4 backdrop-blur-sm transition-colors hover:bg-white/[0.07] ${colors.border}`}
                >
                  {/* Category + severity */}
                  <div className="mb-3 flex items-center justify-between">
                    <span className="text-xs text-white/40">
                      {CATEGORY_ICONS[signal.category] || "📌"} {CATEGORY_LABELS[signal.category] || signal.category}
                    </span>
                    <span className={`rounded-full px-2 py-0.5 text-xs capitalize ${colors.bg} ${colors.text}`}>
                      {signal.severity}
                    </span>
                  </div>

                  {/* Title */}
                  <h3 className="mb-2 text-sm font-medium leading-snug">{signal.title}</h3>

                  {/* Description */}
                  {signal.description && (
                    <p className="mb-3 flex-1 text-xs leading-relaxed text-white/55">{signal.description}</p>
                  )}

                  {/* Meta */}
                  <div className="mb-3 flex items-center gap-3 text-xs text-white/35">
                    {signal.deal_value && <span>{formatCurrency(signal.deal_value)}</span>}
                    {signal.entity_name && <span>· {signal.entity_name}</span>}
                    <span className="ml-auto">{formatTimeAgo(signal.created_at)}</span>
                  </div>

                  {/* Actions */}
                  <div className="flex gap-2">
                    {signal.action_label && (
                      <button
                        onClick={() => handleAction(signal, "actioned")}
                        className="flex flex-1 items-center justify-center gap-1.5 rounded-xl bg-[#f97316]/10 px-3 py-2 text-xs text-[#f97316] transition-colors hover:bg-[#f97316]/20"
                      >
                        {signal.action_label} <ArrowRight className="h-3 w-3" />
                      </button>
                    )}
                    <button
                      onClick={() => handleAction(signal, "dismissed")}
                      className="rounded-xl border border-white/10 px-3 py-2 text-xs text-white/40 transition-colors hover:bg-white/5"
                    >
                      Dismiss
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}

const MOCK_SIGNALS: Signal[] = [
  { id: "1", signal_type: "deal_stalled_14d", category: "deal_health", severity: "critical", title: "TechFlow Inc stalled 14 days", description: "No CRM activity. Deal value $125K.", entity_type: "deal", entity_name: "TechFlow Inc", deal_value: 125000, action_label: "Draft re-engagement email", action_type: "ai_draft", status: "pending", source: "ai", created_at: new Date(Date.now() - 3600000).toISOString() },
  { id: "2", signal_type: "pricing_page_visit", category: "buying_signal", severity: "high", title: "Acme Corp visited pricing 12x", description: "Strong buying intent. 3 stakeholders engaged.", entity_type: "deal", entity_name: "Acme Corp", deal_value: 165000, action_label: "Schedule discovery call", action_type: "schedule", status: "pending", source: "ai", created_at: new Date(Date.now() - 7200000).toISOString() },
  { id: "3", signal_type: "renewal_critical", category: "churn_risk", severity: "critical", title: "DataSync renewal — 12 days left", description: "Champion left company. $95K ARR at risk.", entity_type: "deal", entity_name: "DataSync Corp", deal_value: 95000, action_label: "Identify new champion", action_type: "workflow", status: "pending", source: "ai", created_at: new Date(Date.now() - 10800000).toISOString() },
  { id: "4", signal_type: "pipeline_at_risk_high", category: "pipeline_health", severity: "high", title: "$460K pipeline at critical risk", description: "4 high-value deals with health score below 40.", entity_type: "pipeline", entity_name: "Pipeline", deal_value: 460000, action_label: "Priority intervention list", action_type: "workflow", status: "pending", source: "ai", created_at: new Date(Date.now() - 14400000).toISOString() },
  { id: "5", signal_type: "rep_activity_gap", category: "rep_performance", severity: "medium", title: "Mike Chen — no CRM activity 7d", description: "3 deals totalling $280K with no recent activity.", entity_type: "rep", entity_name: "Mike Chen", deal_value: 280000, action_label: "Manager check-in", action_type: "task", status: "pending", source: "ai", created_at: new Date(Date.now() - 18000000).toISOString() },
  { id: "6", signal_type: "ai_deal_risk_forecast", category: "ai_insight", severity: "high", title: "AI flags 3 deals likely to slip", description: "ML model predicts 3 deals will miss this quarter's close date.", entity_type: "pipeline", entity_name: "Pipeline", deal_value: null, action_label: "Review AI analysis", action_type: "ai_draft", status: "pending", source: "ai", created_at: new Date(Date.now() - 21600000).toISOString() },
];
