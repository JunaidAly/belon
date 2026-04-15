"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Activity, GitBranch, Zap, Settings, Radio } from "lucide-react";
import { cn } from "@/lib/utils";

const NAV = [
  { href: "/control-center",  label: "Control Center",   short: "Center",  icon: Activity },
  { href: "/workflow-builder", label: "Workflow Builder", short: "Flows",   icon: GitBranch },
  { href: "/signals",          label: "Signal Feed",      short: "Signals", icon: Radio },
  { href: "/integrations",     label: "Integrations",     short: "Apps",    icon: Settings },
] as const;

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <>
      {/* Desktop rail */}
      <aside className="hidden shrink-0 flex-col items-center border-r border-white/5 bg-[#0d0e1a]/80 py-5 md:flex md:w-16 lg:w-20">
        {/* Logo */}
        <Link href="/control-center" className="mb-8 flex h-10 w-10 items-center justify-center rounded-xl bg-[#f97316] transition-opacity hover:opacity-90">
          <Zap className="h-5 w-5 text-black" strokeWidth={2.5} />
        </Link>

        <nav className="flex flex-1 flex-col gap-3">
          {NAV.map(({ href, label, icon: Icon }) => {
            const active = pathname.startsWith(href);
            return (
              <Link
                key={href}
                href={href}
                title={label}
                className={cn(
                  "group relative flex h-11 w-11 items-center justify-center rounded-xl transition-colors",
                  active
                    ? "bg-[#f97316] text-black shadow-lg shadow-[#f97316]/20"
                    : "text-white/50 hover:bg-white/10 hover:text-white"
                )}
              >
                <Icon className="h-5 w-5" strokeWidth={active ? 2.5 : 2} />
                {/* Tooltip */}
                <span className="pointer-events-none absolute left-full z-50 ml-3 hidden whitespace-nowrap rounded-lg border border-white/10 bg-[#0d0e1a] px-3 py-1.5 text-xs text-white opacity-0 transition-opacity group-hover:block group-hover:opacity-100">
                  {label}
                </span>
              </Link>
            );
          })}
        </nav>

        {/* Live indicator */}
        <div className="mb-1 flex flex-col items-center gap-1" title="Agent active">
          <div className="h-1.5 w-1.5 animate-pulse rounded-full bg-emerald-500" />
          <span className="text-[10px] text-white/30">Live</span>
        </div>
      </aside>

      {/* Mobile bottom nav */}
      <nav className="fixed bottom-0 left-0 right-0 z-30 grid grid-cols-4 border-t border-white/5 bg-[#0d0e1a]/95 pb-safe-bottom backdrop-blur-xl md:hidden">
        {NAV.map(({ href, label, short, icon: Icon }) => {
          const active = pathname.startsWith(href);
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex min-h-[3.25rem] flex-col items-center justify-center gap-0.5 px-1 py-2 text-center transition-colors",
                active ? "text-[#f97316]" : "text-white/40"
              )}
            >
              <Icon className="h-5 w-5 shrink-0" strokeWidth={active ? 2.5 : 2} />
              <span className="text-[0.6rem] leading-tight">{short}</span>
            </Link>
          );
        })}
      </nav>
    </>
  );
}
