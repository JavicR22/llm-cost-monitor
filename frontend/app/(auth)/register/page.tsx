"use client";

import Link from "next/link";
import { useState } from "react";
import { AuthBranding } from "@/components/auth/AuthBranding";
import { apiClient } from "@/lib/api";

interface RegisterResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export default function RegisterPage() {
  const [form, setForm] = useState({
    fullName: "",
    orgName: "",
    email: "",
    password: "",
  });
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");

    if (form.password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }

    setLoading(true);
    try {
      const data = await apiClient<RegisterResponse>("/api/v1/auth/register", {
        method: "POST",
        body: JSON.stringify({
          name: form.fullName,
          org_name: form.orgName,
          email: form.email,
          password: form.password,
        }),
      });
      localStorage.setItem("access_token", data.access_token);
      document.cookie = `llm_monitor_token=${data.access_token}; path=/; max-age=604800; SameSite=Strict`;
      window.location.href = "/dashboard";
    } catch (err) {
      setError(err instanceof Error ? err.message : "Registration failed. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  const passwordStrength = getPasswordStrength(form.password);

  return (
    <div className="flex h-screen w-full">
      {/* Left: Branding */}
      <div className="w-1/2">
        <AuthBranding />
      </div>

      {/* Right: Form */}
      <div className="relative flex w-1/2 flex-col items-center justify-center overflow-y-auto bg-[#1E293B] px-12 py-10">
        {/* Top accent line */}
        <div className="absolute inset-x-0 top-0 h-1.5 bg-[#3B82F6]" />

        <div className="w-full max-w-md space-y-7">
          {/* Header */}
          <div className="space-y-2">
            <h2 className="text-3xl font-bold text-white">Create your account</h2>
            <p className="text-base text-[#94A3B8]">Start monitoring your LLM costs for free</p>
          </div>

          {/* Social signup */}
          <div className="grid grid-cols-2 gap-4">
            <button
              type="button"
              className="flex items-center justify-center gap-2 rounded-xl bg-[#0F172A] px-4 py-2.5 text-sm font-semibold text-[#E2E8F0] transition-colors hover:bg-[#0a101f]"
            >
              <GoogleIcon />
              Google
            </button>
            <button
              type="button"
              className="flex items-center justify-center gap-2 rounded-xl bg-[#0F172A] px-4 py-2.5 text-sm font-semibold text-[#E2E8F0] transition-colors hover:bg-[#0a101f]"
            >
              <GitHubIcon />
              GitHub
            </button>
          </div>

          {/* Divider */}
          <div className="relative flex items-center">
            <div className="flex-1 border-t border-[#334155]" />
            <span className="bg-[#1E293B] px-4 text-sm text-[#64748B]">or</span>
            <div className="flex-1 border-t border-[#334155]" />
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-5">
            {error && (
              <div className="rounded-lg bg-[#EF4444]/10 px-4 py-3 text-sm text-[#F87171]">
                {error}
              </div>
            )}

            {/* Full name + Org name */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <label className="block text-sm font-medium text-[#CBD5E1]">
                  Full name
                </label>
                <input
                  name="fullName"
                  type="text"
                  required
                  value={form.fullName}
                  onChange={handleChange}
                  placeholder="Alex Rivera"
                  className="w-full rounded-xl bg-[#0F172A] px-4 py-3 text-sm text-[#F8FAFC] placeholder-[#475569] outline-none ring-1 ring-[#334155] transition focus:ring-2 focus:ring-[#3B82F6]"
                />
              </div>
              <div className="space-y-1.5">
                <label className="block text-sm font-medium text-[#CBD5E1]">
                  Company name
                </label>
                <input
                  name="orgName"
                  type="text"
                  required
                  value={form.orgName}
                  onChange={handleChange}
                  placeholder="Acme Inc."
                  className="w-full rounded-xl bg-[#0F172A] px-4 py-3 text-sm text-[#F8FAFC] placeholder-[#475569] outline-none ring-1 ring-[#334155] transition focus:ring-2 focus:ring-[#3B82F6]"
                />
              </div>
            </div>

            {/* Email */}
            <div className="space-y-1.5">
              <label className="block text-sm font-medium text-[#CBD5E1]">
                Work email
              </label>
              <input
                name="email"
                type="email"
                required
                value={form.email}
                onChange={handleChange}
                placeholder="you@company.com"
                className="w-full rounded-xl bg-[#0F172A] px-4 py-3 text-sm text-[#F8FAFC] placeholder-[#475569] outline-none ring-1 ring-[#334155] transition focus:ring-2 focus:ring-[#3B82F6]"
              />
            </div>

            {/* Password */}
            <div className="space-y-1.5">
              <label className="block text-sm font-medium text-[#CBD5E1]">
                Password
              </label>
              <div className="relative">
                <input
                  name="password"
                  type={showPassword ? "text" : "password"}
                  required
                  value={form.password}
                  onChange={handleChange}
                  placeholder="Min. 8 characters"
                  className="w-full rounded-xl bg-[#0F172A] px-4 py-3 pr-11 text-sm text-[#F8FAFC] placeholder-[#475569] outline-none ring-1 ring-[#334155] transition focus:ring-2 focus:ring-[#3B82F6]"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((v) => !v)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-[#64748B] hover:text-[#94A3B8]"
                  aria-label={showPassword ? "Hide password" : "Show password"}
                >
                  {showPassword ? <EyeOffIcon /> : <EyeIcon />}
                </button>
              </div>

              {/* Password strength bar */}
              {form.password.length > 0 && (
                <div className="space-y-1">
                  <div className="flex gap-1">
                    {[1, 2, 3, 4].map((level) => (
                      <div
                        key={level}
                        className="h-1 flex-1 rounded-full transition-colors"
                        style={{
                          backgroundColor:
                            passwordStrength.score >= level
                              ? passwordStrength.color
                              : "#1E293B",
                        }}
                      />
                    ))}
                  </div>
                  <p className="text-xs" style={{ color: passwordStrength.color }}>
                    {passwordStrength.label}
                  </p>
                </div>
              )}
            </div>

            {/* Terms */}
            <p className="text-xs text-[#64748B]">
              By creating an account you agree to our{" "}
              <Link href="#" className="text-[#60A5FA] hover:underline">
                Terms of Service
              </Link>{" "}
              and{" "}
              <Link href="#" className="text-[#60A5FA] hover:underline">
                Privacy Policy
              </Link>
              .
            </p>

            {/* Submit */}
            <button
              type="submit"
              disabled={loading}
              className="flex w-full items-center justify-center gap-2 rounded-xl bg-[#3B82F6] px-4 py-3 text-sm font-bold text-white transition-colors hover:bg-[#2563EB] disabled:opacity-60"
            >
              {loading ? <Spinner /> : null}
              Create Account
            </button>
          </form>

          {/* Footer */}
          <p className="text-center text-sm text-[#94A3B8]">
            Already have an account?{" "}
            <Link
              href="/login"
              className="font-semibold text-[#60A5FA] hover:text-[#3B82F6]"
            >
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}

function getPasswordStrength(password: string): {
  score: number;
  label: string;
  color: string;
} {
  if (password.length === 0) return { score: 0, label: "", color: "" };
  let score = 0;
  if (password.length >= 8) score++;
  if (/[A-Z]/.test(password)) score++;
  if (/[0-9]/.test(password)) score++;
  if (/[^A-Za-z0-9]/.test(password)) score++;

  const map = [
    { label: "Too weak", color: "#EF4444" },
    { label: "Weak", color: "#F59E0B" },
    { label: "Fair", color: "#F59E0B" },
    { label: "Strong", color: "#10B981" },
    { label: "Very strong", color: "#10B981" },
  ];
  return { score, ...map[score] };
}

function GoogleIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24">
      <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
      <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
      <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
      <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
    </svg>
  );
}

function GitHubIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
      <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z" />
    </svg>
  );
}

function EyeIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
      <circle cx="12" cy="12" r="3" />
    </svg>
  );
}

function EyeOffIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24" />
      <line x1="1" y1="1" x2="23" y2="23" />
    </svg>
  );
}

function Spinner() {
  return (
    <svg className="animate-spin" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M21 12a9 9 0 1 1-6.219-8.56" />
    </svg>
  );
}
