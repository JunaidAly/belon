"use client";
import { useEffect, useState } from "react";
import { CheckCircle2, Circle, Settings, ExternalLink, RefreshCw, Loader2, Zap } from "lucide-react";
import { toast } from "sonner";
import { integrationsApi, type Integration } from "@/lib/api";
import { formatTimeAgo } from "@/lib/utils";

const ALL_INTEGRATIONS = [
  { provider: "hubspot",   name: "HubSpot",               desc: "Two-way sync of contacts, deals, and activities",  emoji: "🟠", priority: true },
  { provider: "salesforce",name: "Salesforce",             desc: "Full CRM data synchronization",                    emoji: "☁️", priority: false },
  { provider: "gmail",     name: "Gmail",                  desc: "Email tracking, logging, and auto-response",       emoji: "📧", priority: false },
  { provider: "slack",     name: "Slack",                  desc: "Real-time pipeline alerts and notifications",       emoji: "💬", priority: false },
  { provider: "zoom",      name: "Zoom",                   desc: "Meeting scheduling, recordings, and AI summaries", emoji: "📹", priority: false },
  { provider: "linkedin",  name: "LinkedIn Sales Nav",     desc: "Prospect research and buying signal enrichment",    emoji: "💼", priority: false },
  { provider: "pipedrive", name: "Pipedrive",              desc: "Full pipeline and deal synchronization",            emoji: "🔄", priority: false },
];

export default function IntegrationsPage() {
  const [integrations, setIntegrations] = useState<Integration[]>([]);
  const [syncing, setSyncing] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    integrationsApi.list()
      .then(setIntegrations)
      .catch(() => setIntegrations([]))
      .finally(() => setLoading(false));
  }, []);

  const getStatus = (provider: string) =>
    integrations.find((i) => i.provider === provider);

  const handleConnect = async (provider: string) => {
    if (provider === "hubspot") {
      try {
        const { auth_url } = await integrationsApi.hubspotConnect();
        window.open(auth_url, "_blank", "width=600,height=700");
        toast.info("HubSpot auth opened in new window");
      } catch {
        toast.error("Failed to start HubSpot connection");
      }
    } else {
      toast.info(`${provider} integration coming soon — join the waitlist.`);
    }
  };

  const handleDisconnect = async (provider: string) => {
    try {
      await integrationsApi.disconnect(provider);
      setIntegrations((prev) => prev.filter((i) => i.provider !== provider));
      toast.success(`${provider} disconnected`);
    } catch {
      toast.error("Disconnect failed");
    }
  };

  const handleSync = async (provider: string) => {
    setSyncing(provider);
    try {
      if (provider === "hubspot") {
        await integrationsApi.hubspotSync();
        // Refresh integration status
        const status = await integrationsApi.status(provider);
        setIntegrations((prev) =>
          prev.map((i) => i.provider === provider ? { ...i, ...status, last_sync_at: new Date().toISOString() } : i)
        );
        toast.success("HubSpot sync complete");
      }
    } catch {
      toast.error("Sync failed");
    } finally {
      setSyncing(null);
    }
  };

  const connectedCount = ALL_INTEGRATIONS.filter((i) => getStatus(i.provider)?.status === "connected").length;

  return (
    <div className="mx-auto w-full max-w-7xl px-4 py-6 sm:p-6 lg:p-8">
      {/* Header */}
      <div className="belon-enter-up mb-6 sm:mb-8">
        <h1 className="mb-1 text-2xl font-medium sm:text-3xl">Integrations Hub</h1>
        <p className="text-white/55">
          {ALL_INTEGRATIONS.length} integrations available ·{" "}
          <span className="text-emerald-400">{connectedCount} connected</span>
        </p>
      </div>

      {loading ? (
        <div className="flex justify-center py-20">
          <Loader2 className="h-8 w-8 animate-spin text-[#f97316]" />
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {ALL_INTEGRATIONS.map((intgr, i) => {
            const status = getStatus(intgr.provider);
            const connected = status?.status === "connected";

            return (
              <div
                key={intgr.provider}
                style={{ animationDelay: `${i * 50}ms` }}
                className={`belon-enter-up rounded-2xl border bg-white/5 p-5 backdrop-blur-sm transition-colors hover:bg-white/[0.07] ${
                  connected ? "border-emerald-500/25" : "border-white/10"
                }`}
              >
                {/* Header */}
                <div className="mb-4 flex items-start justify-between">
                  <div className="flex h-14 w-14 items-center justify-center rounded-xl bg-white/10 text-3xl">
                    {intgr.emoji}
                  </div>
                  <div className="flex items-center gap-2">
                    {connected && <div className="h-2 w-2 animate-pulse rounded-full bg-emerald-500" />}
                    {intgr.priority && !connected && (
                      <span className="rounded-full border border-[#f97316]/20 bg-[#f97316]/10 px-2 py-0.5 text-xs text-[#f97316]">
                        Priority
                      </span>
                    )}
                    {connected ? (
                      <CheckCircle2 className="h-5 w-5 text-emerald-400" />
                    ) : (
                      <Circle className="h-5 w-5 text-white/20" />
                    )}
                  </div>
                </div>

                <h3 className="mb-1 text-base font-medium">{intgr.name}</h3>
                <p className="mb-4 text-sm leading-relaxed text-white/55">{intgr.desc}</p>

                {/* Sync status */}
                {connected && status && (
                  <div className="mb-4 border-b border-white/5 pb-4">
                    <div className="text-xs text-white/40">Last synced</div>
                    <div className="text-sm text-white/70">
                      {status.last_sync_at ? formatTimeAgo(status.last_sync_at) : "Never"}
                      {status.records_synced > 0 && ` · ${status.records_synced.toLocaleString()} records`}
                    </div>
                  </div>
                )}

                {/* Actions */}
                <div className="flex flex-wrap gap-2">
                  {connected ? (
                    <>
                      <button
                        onClick={() => handleSync(intgr.provider)}
                        disabled={syncing === intgr.provider}
                        className="flex min-h-10 flex-1 items-center justify-center gap-1.5 rounded-xl border border-white/10 bg-white/10 px-3 py-2 text-sm transition-colors hover:bg-white/15 disabled:opacity-50"
                      >
                        {syncing === intgr.provider ? (
                          <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                          <RefreshCw className="h-4 w-4" />
                        )}
                        Sync Now
                      </button>
                      <button
                        onClick={() => toast.info("Settings coming soon")}
                        className="flex min-h-10 min-w-10 items-center justify-center rounded-xl border border-white/10 bg-white/5 px-3 py-2 transition-colors hover:bg-white/10"
                      >
                        <Settings className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => handleDisconnect(intgr.provider)}
                        className="min-h-10 w-full rounded-xl border border-white/10 px-3 py-2 text-sm text-white/50 transition-colors hover:bg-red-500/20 hover:text-red-300"
                      >
                        Disconnect
                      </button>
                    </>
                  ) : (
                    <button
                      onClick={() => handleConnect(intgr.provider)}
                      className="min-h-10 w-full rounded-xl bg-[#f97316] px-4 py-2 text-sm font-medium text-black transition-opacity hover:opacity-90"
                    >
                      {intgr.priority ? "Connect HubSpot" : "Connect"}
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* About */}
      <div className="belon-enter-up mt-10 rounded-2xl border border-white/10 bg-white/5 p-6 backdrop-blur-sm">
        <div className="mb-4 flex items-center gap-2">
          <Zap className="h-5 w-5 text-[#f97316]" />
          <h3 className="font-medium">About Belon Integrations</h3>
        </div>
        <p className="mb-6 leading-relaxed text-sm text-white/55">
          Belon connects to your existing stack and syncs data bidirectionally. The AI signal engine uses this data to detect buying signals, churn risk, and pipeline health issues — all in real time.
        </p>
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-3">
          {[
            { title: "Real-time Sync", desc: "All integrations sync data every 15 minutes with no manual intervention." },
            { title: "Secure & Encrypted", desc: "OAuth 2.0 for all connections. Tokens encrypted at rest." },
            { title: "Custom Mappings", desc: "Configure field mappings and sync rules to match your workflow." },
          ].map((item) => (
            <div key={item.title}>
              <div className="mb-1 font-medium">{item.title}</div>
              <div className="text-sm text-white/55">{item.desc}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
