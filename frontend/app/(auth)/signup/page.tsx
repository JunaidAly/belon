"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Mail, Lock, User, Building2, ArrowRight, Loader2, CheckCircle2 } from "lucide-react";
import { supabase } from "@/lib/supabase";
import { toast } from "sonner";

const TRIAL_PERKS = [
  "100+ AI signals monitoring your pipeline",
  "6 pre-built automation workflows",
  "HubSpot two-way sync",
  "Visual workflow builder",
];

export default function SignupPage() {
  const router = useRouter();
  const [form, setForm] = useState({ name: "", company: "", email: "", password: "" });
  const [loading, setLoading] = useState(false);

  const set = (k: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm((f) => ({ ...f, [k]: e.target.value }));

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.email || !form.password || !form.name) return;
    setLoading(true);
    try {
      const { error } = await supabase.auth.signUp({
        email: form.email,
        password: form.password,
        options: {
          data: { full_name: form.name, company_name: form.company },
          emailRedirectTo: `${window.location.origin}/control-center`,
        },
      });
      if (error) throw error;
      toast.success("Account created! Check your email to verify.");
      router.push("/control-center");
    } catch (err: unknown) {
      toast.error((err as Error).message || "Signup failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Trial perks */}
      <div className="rounded-xl border border-[#f97316]/20 bg-[#f97316]/5 p-4">
        <p className="mb-3 text-sm font-medium text-[#f97316]">5-day free trial · then $1,000/year</p>
        <ul className="space-y-1.5">
          {TRIAL_PERKS.map((p) => (
            <li key={p} className="flex items-center gap-2 text-xs text-white/60">
              <CheckCircle2 className="h-3.5 w-3.5 shrink-0 text-[#f97316]" />
              {p}
            </li>
          ))}
        </ul>
      </div>

      <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-8">
        <h2 className="mb-1 text-xl font-medium">Create account</h2>
        <p className="mb-6 text-sm text-white/50">No credit card required for trial.</p>

        <form onSubmit={handleSignup} className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <label className="text-xs text-white/60">Full name</label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-white/40" />
                <input
                  type="text"
                  value={form.name}
                  onChange={set("name")}
                  placeholder="Sarah Johnson"
                  required
                  className="w-full rounded-xl border border-white/10 bg-white/5 py-2.5 pl-9 pr-3 text-sm placeholder:text-white/30 focus:border-[#f97316]/50 focus:bg-white/[0.07] focus:outline-none"
                />
              </div>
            </div>
            <div className="space-y-1.5">
              <label className="text-xs text-white/60">Company</label>
              <div className="relative">
                <Building2 className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-white/40" />
                <input
                  type="text"
                  value={form.company}
                  onChange={set("company")}
                  placeholder="Acme Inc"
                  className="w-full rounded-xl border border-white/10 bg-white/5 py-2.5 pl-9 pr-3 text-sm placeholder:text-white/30 focus:border-[#f97316]/50 focus:bg-white/[0.07] focus:outline-none"
                />
              </div>
            </div>
          </div>

          <div className="space-y-1.5">
            <label className="text-xs text-white/60">Work email</label>
            <div className="relative">
              <Mail className="absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-white/40" />
              <input
                type="email"
                value={form.email}
                onChange={set("email")}
                placeholder="you@company.com"
                required
                className="w-full rounded-xl border border-white/10 bg-white/5 py-3 pl-10 pr-4 text-sm placeholder:text-white/30 focus:border-[#f97316]/50 focus:bg-white/[0.07] focus:outline-none"
              />
            </div>
          </div>

          <div className="space-y-1.5">
            <label className="text-xs text-white/60">Password</label>
            <div className="relative">
              <Lock className="absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-white/40" />
              <input
                type="password"
                value={form.password}
                onChange={set("password")}
                placeholder="Min. 8 characters"
                required
                minLength={8}
                className="w-full rounded-xl border border-white/10 bg-white/5 py-3 pl-10 pr-4 text-sm placeholder:text-white/30 focus:border-[#f97316]/50 focus:bg-white/[0.07] focus:outline-none"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="flex w-full items-center justify-center gap-2 rounded-xl bg-[#f97316] py-3 text-sm font-medium text-black transition-opacity hover:opacity-90 disabled:opacity-60"
          >
            {loading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <>
                Start free trial <ArrowRight className="h-4 w-4" />
              </>
            )}
          </button>
        </form>

        <p className="mt-4 text-center text-xs text-white/30">
          By creating an account you agree to our Terms of Service.
        </p>

        <div className="mt-4 text-center text-sm text-white/40">
          Already have an account?{" "}
          <Link href="/login" className="text-[#f97316] hover:text-[#f97316]/80">
            Sign in
          </Link>
        </div>
      </div>
    </div>
  );
}
