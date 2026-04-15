"use client";
import { useEffect, useState } from "react";
import { CheckCircle2, Zap, Loader2 } from "lucide-react";
import { billingApi } from "@/lib/api";
import { toast } from "sonner";

const FEATURES = [
  "100+ AI-powered pipeline signals",
  "6 pre-built automation workflows",
  "Visual Workflow Builder (React Flow)",
  "HubSpot two-way sync",
  "Signal Intelligence Feed (real-time)",
  "AI email drafting (Falcon-7B)",
  "Lead scoring & deal health analysis",
  "Churn prediction & buying signal detection",
  "Rep performance monitoring",
  "Unlimited workflow runs",
  "Slack & Gmail notifications",
  "Priority support",
];

export default function BillingPage() {
  const [subscription, setSubscription] = useState<{ status: string; trial_end?: string; current_period_end?: string } | null>(null);
  const [loading, setLoading] = useState(true);
  const [checkoutLoading, setCheckoutLoading] = useState(false);

  useEffect(() => {
    billingApi.subscription()
      .then((s) => setSubscription(s as typeof subscription))
      .catch(() => setSubscription({ status: "trialing" }))
      .finally(() => setLoading(false));
  }, []);

  const handleUpgrade = async () => {
    setCheckoutLoading(true);
    try {
      const { checkout_url } = await billingApi.createCheckout(
        `${window.location.origin}/billing?success=1`,
        `${window.location.origin}/billing`,
      );
      window.location.href = checkout_url;
    } catch {
      toast.error("Failed to open checkout");
      setCheckoutLoading(false);
    }
  };

  const handlePortal = async () => {
    try {
      const { portal_url } = await billingApi.portal(window.location.href);
      window.location.href = portal_url;
    } catch {
      toast.error("Billing portal unavailable");
    }
  };

  return (
    <div className="mx-auto max-w-3xl px-4 py-10 sm:px-6 lg:px-8">
      <div className="belon-enter-up mb-8">
        <h1 className="mb-1 text-2xl font-medium sm:text-3xl">Billing & Subscription</h1>
        {!loading && subscription && (
          <p className="text-white/55 capitalize">Status: <span className="text-[#f97316]">{subscription.status}</span></p>
        )}
      </div>

      {/* Plan card */}
      <div className="belon-enter-up mb-6 rounded-2xl border border-[#f97316]/25 bg-[#f97316]/5 p-6 sm:p-8">
        <div className="mb-4 flex items-start justify-between">
          <div>
            <div className="mb-1 flex items-center gap-2">
              <Zap className="h-5 w-5 text-[#f97316]" />
              <h2 className="text-lg font-semibold">Belon Pro</h2>
            </div>
            <div className="text-3xl font-semibold">$1,000<span className="text-base font-normal text-white/50">/year</span></div>
            <div className="mt-1 text-sm text-white/50">Less than $3/day for a fully autonomous AI CRM</div>
          </div>
          {subscription?.status === "trialing" && (
            <span className="rounded-full border border-[#f97316]/20 bg-[#f97316]/10 px-3 py-1 text-sm text-[#f97316]">
              5-day free trial
            </span>
          )}
          {subscription?.status === "active" && (
            <span className="rounded-full border border-emerald-500/20 bg-emerald-500/10 px-3 py-1 text-sm text-emerald-400">
              ✓ Active
            </span>
          )}
        </div>

        <ul className="mb-6 grid grid-cols-1 gap-2 sm:grid-cols-2">
          {FEATURES.map((f) => (
            <li key={f} className="flex items-start gap-2 text-sm text-white/65">
              <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-[#f97316]" />
              {f}
            </li>
          ))}
        </ul>

        {loading ? (
          <div className="flex justify-center py-4"><Loader2 className="h-6 w-6 animate-spin text-[#f97316]" /></div>
        ) : subscription?.status === "active" ? (
          <button onClick={handlePortal}
            className="w-full rounded-xl border border-white/10 bg-white/10 py-3 text-sm font-medium transition-colors hover:bg-white/15">
            Manage Subscription →
          </button>
        ) : (
          <button onClick={handleUpgrade} disabled={checkoutLoading}
            className="flex w-full items-center justify-center gap-2 rounded-xl bg-[#f97316] py-3 text-sm font-semibold text-black transition-opacity hover:opacity-90 disabled:opacity-60">
            {checkoutLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
            {subscription?.status === "trialing" ? "Start Subscription — $1,000/year" : "Reactivate Plan"}
          </button>
        )}
      </div>

      <p className="text-center text-xs text-white/30">
        Cancel anytime. No hidden fees. Secure payments via Stripe.
      </p>
    </div>
  );
}
