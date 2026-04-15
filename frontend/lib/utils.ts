import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatCurrency(value: number): string {
  if (value >= 1_000_000) return `$${(value / 1_000_000).toFixed(1)}M`;
  if (value >= 1_000) return `$${(value / 1_000).toFixed(0)}K`;
  return `$${value.toFixed(0)}`;
}

export function formatTimeAgo(dateStr: string): string {
  const now = new Date();
  const date = new Date(dateStr);
  const diff = Math.floor((now.getTime() - date.getTime()) / 1000);
  if (diff < 60) return "just now";
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return `${Math.floor(diff / 86400)}d ago`;
}

export const SEVERITY_COLORS = {
  critical: { bg: "bg-red-500/10", text: "text-red-400", border: "border-red-500/30" },
  high: { bg: "bg-orange-500/10", text: "text-orange-400", border: "border-orange-500/30" },
  medium: { bg: "bg-amber-500/10", text: "text-amber-400", border: "border-amber-500/30" },
  low: { bg: "bg-emerald-500/10", text: "text-emerald-400", border: "border-emerald-500/30" },
  info: { bg: "bg-white/5", text: "text-white/60", border: "border-white/10" },
} as const;

export const CATEGORY_LABELS: Record<string, string> = {
  deal_health: "Deal Health",
  buying_signal: "Buying Signal",
  churn_risk: "Churn Risk",
  rep_performance: "Rep Performance",
  pipeline_health: "Pipeline",
  engagement: "Engagement",
  ai_insight: "AI Insight",
};
