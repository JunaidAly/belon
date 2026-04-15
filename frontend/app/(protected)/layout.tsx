import { createSupabaseServer } from "@/lib/supabase-server";
import { redirect } from "next/navigation";
import Sidebar from "@/components/layout/Sidebar";
import Header from "@/components/layout/Header";

export default async function ProtectedLayout({ children }: { children: React.ReactNode }) {
  const supabase = createSupabaseServer();
  const { data: { user } } = await supabase.auth.getUser();

  if (!user) redirect("/login");

  // Fetch profile + subscription
  const [profileResp, subResp] = await Promise.all([
    supabase.from("profiles").select("full_name, email").eq("id", user.id).single(),
    supabase.from("subscriptions").select("status, trial_end").eq("user_id", user.id).single(),
  ]);

  const profile = profileResp.data;
  const subscription = subResp.data;

  return (
    <div className="flex h-dvh min-h-0 bg-[#080808] text-white">
      <Sidebar />
      <div className="flex min-h-0 min-w-0 flex-1 flex-col overflow-hidden">
        <Header
          userName={profile?.full_name || user.email?.split("@")[0] || "User"}
          subscriptionStatus={subscription?.status || "trialing"}
          trialEnd={subscription?.trial_end || null}
        />
        <main className="belon-scroll min-h-0 flex-1 overflow-x-hidden overflow-y-auto">
          {children}
        </main>
      </div>
    </div>
  );
}
