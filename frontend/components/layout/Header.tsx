"use client";
import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { LogOut, CreditCard, ChevronDown, Zap } from "lucide-react";
import { supabase } from "@/lib/supabase";
import { billingApi } from "@/lib/api";
import { toast } from "sonner";
import { cn } from "@/lib/utils";
import { format, parseISO, differenceInDays } from "date-fns";

interface HeaderProps {
  userName: string;
  subscriptionStatus: string;
  trialEnd: string | null;
}

export default function Header({ userName, subscriptionStatus, trialEnd }: HeaderProps) {
  const router = useRouter();
  const [menuOpen, setMenuOpen] = useState(false);
  const initials = userName.split(" ").map((n) => n[0]).join("").toUpperCase().slice(0, 2);

  const trialDaysLeft = trialEnd
    ? Math.max(0, differenceInDays(parseISO(trialEnd), new Date()))
    : null;

  const handleSignOut = async () => {
    await supabase.auth.signOut();
    router.push("/login");
    router.refresh();
  };

  const handleBillingPortal = async () => {
    try {
      const { portal_url } = await billingApi.portal(window.location.href);
      window.location.href = portal_url;
    } catch {
      toast.error("Billing portal unavailable");
    }
  };

  return (
    <header className="flex h-14 shrink-0 items-center justify-between gap-4 border-b border-white/5 bg-[#080808]/80 px-4 backdrop-blur-xl sm:px-6 md:h-14 lg:px-8">
      {/* Left: brand + live status */}
      <div className="flex items-center gap-3">
        {/* Mobile logo */}
        <Link href="/control-center" className="flex h-8 w-8 items-center justify-center rounded-lg bg-[#f97316] md:hidden">
          <Zap className="h-4 w-4 text-black" strokeWidth={2.5} />
        </Link>
        <h1 className="text-base font-medium tracking-tight md:text-lg">Belon</h1>
        <div className="hidden items-center gap-1.5 rounded-full border border-emerald-500/20 bg-emerald-500/10 px-2.5 py-1 sm:flex">
          <div className="h-1.5 w-1.5 animate-pulse rounded-full bg-emerald-500" />
          <span className="text-xs text-emerald-400">Agent Active</span>
        </div>
      </div>

      {/* Right */}
      <div className="flex items-center gap-3">
        {/* Trial banner */}
        {subscriptionStatus === "trialing" && trialDaysLeft !== null && (
          <Link
            href="/billing"
            className="hidden items-center gap-1.5 rounded-full border border-[#f97316]/20 bg-[#f97316]/10 px-3 py-1 text-xs text-[#f97316] transition-colors hover:bg-[#f97316]/20 sm:flex"
          >
            <span>{trialDaysLeft}d trial left</span>
            <span>· Upgrade</span>
          </Link>
        )}

        {/* Avatar menu */}
        <div className="relative">
          <button
            onClick={() => setMenuOpen(!menuOpen)}
            className="flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 py-1.5 pl-1.5 pr-3 transition-colors hover:bg-white/10"
          >
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-[#f97316] text-xs font-semibold text-black">
              {initials}
            </div>
            <span className="hidden text-sm text-white/70 sm:inline">{userName.split(" ")[0]}</span>
            <ChevronDown className={cn("h-3.5 w-3.5 text-white/40 transition-transform", menuOpen && "rotate-180")} />
          </button>

          {menuOpen && (
            <>
              <div className="fixed inset-0 z-40" onClick={() => setMenuOpen(false)} />
              <div className="absolute right-0 top-full z-50 mt-2 w-52 rounded-xl border border-white/10 bg-[#0d0e1a] p-1 shadow-xl">
                <div className="px-3 py-2 text-xs text-white/40">{userName}</div>
                <div className="my-1 h-px bg-white/5" />
                <button
                  onClick={handleBillingPortal}
                  className="flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-sm text-white/70 transition-colors hover:bg-white/10 hover:text-white"
                >
                  <CreditCard className="h-4 w-4" /> Billing
                </button>
                <button
                  onClick={handleSignOut}
                  className="flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-sm text-white/70 transition-colors hover:bg-red-500/20 hover:text-red-300"
                >
                  <LogOut className="h-4 w-4" /> Sign out
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
