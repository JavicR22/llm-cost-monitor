export function AuthBranding() {
  return (
    <div className="relative hidden h-full flex-col justify-between overflow-hidden bg-[#0F172A] p-12 lg:flex">
      {/* Gradient orbs */}
      <div
        aria-hidden
        className="pointer-events-none absolute -left-32 -top-32 h-[500px] w-[500px] rounded-full bg-[#3B82F6] opacity-10 blur-3xl"
      />
      <div
        aria-hidden
        className="pointer-events-none absolute -bottom-24 -right-24 h-[400px] w-[400px] rounded-full bg-[#8B5CF6] opacity-10 blur-3xl"
      />
      <div
        aria-hidden
        className="pointer-events-none absolute left-1/2 top-1/2 h-[300px] w-[300px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-[#3B82F6] opacity-5 blur-2xl"
      />

      {/* Logo */}
      <div className="relative flex items-center gap-3">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-[#3B82F6]">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
          </svg>
        </div>
        <span className="text-xl font-bold text-white">LLM Cost Monitor</span>
      </div>

      {/* Headline */}
      <div className="relative space-y-6">
        <h1 className="text-5xl font-extrabold leading-tight text-white">
          Monitor every token.{" "}
          <span className="text-[#3B82F6]">Optimize</span> every dollar.
        </h1>
        <p className="max-w-md text-xl leading-relaxed text-[#94A3B8]">
          Open-source LLM cost management for developers and startups. Join 200+
          developers shipping with AI.
        </p>

        {/* Social proof */}
        <div className="flex items-center gap-3">
          <div className="flex -space-x-2">
            {["#3B82F6", "#8B5CF6", "#10B981", "#F59E0B"].map((color, i) => (
              <div
                key={i}
                className="flex h-8 w-8 items-center justify-center rounded-full border-2 border-[#0F172A] text-xs font-semibold text-white"
                style={{ backgroundColor: color }}
              >
                {["A", "M", "J", "S"][i]}
              </div>
            ))}
          </div>
          <p className="text-sm text-[#64748B]">
            Trusted by 200+ developers
          </p>
        </div>
      </div>

      {/* Footer */}
      <div className="relative flex items-center gap-4 text-sm text-[#64748B]">
        <span>© 2026 LLM Cost Monitor v1.0</span>
        <span className="h-1 w-1 rounded-full bg-[#334155]" />
        <a href="#" className="hover:text-[#94A3B8]">Privacy Policy</a>
        <span className="h-1 w-1 rounded-full bg-[#334155]" />
        <a href="#" className="hover:text-[#94A3B8]">Terms of Service</a>
      </div>
    </div>
  );
}
