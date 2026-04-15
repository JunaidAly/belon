export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen items-center justify-center bg-[#080808] px-4">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="mb-8 flex flex-col items-center gap-3">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-[#f97316]">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" className="text-black">
              <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" fill="currentColor" strokeLinejoin="round" />
            </svg>
          </div>
          <h1 className="text-2xl font-semibold tracking-tight">Belon</h1>
          <p className="text-sm text-white/50">AI-Powered CRM Pipeline Automation</p>
        </div>
        {children}
      </div>
    </div>
  );
}
