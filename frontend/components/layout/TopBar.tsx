"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

type DateRange = "7d" | "30d" | "custom";

interface TopBarProps {
  orgName?: string;
  workspace?: string;
  notificationCount?: number;
}

export function TopBar({
  orgName = "Acme AI Infrastructure",
  workspace = "Main Workspace",
  notificationCount = 0,
}: TopBarProps) {
  const router = useRouter();
  const [dateRange, setDateRange] = useState<DateRange>("30d");

  function handleLogout() {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    document.cookie = "llm_monitor_token=; path=/; max-age=0";
    router.push("/login");
  }

  return (
    <header className="flex h-16 shrink-0 items-center justify-between border-b border-[#1E293B] bg-[#0F172A] px-8">
      {/* Left: Org breadcrumb */}
      <div className="flex items-center gap-2">
        <span className="text-lg font-semibold text-[#F8FAFC]">{orgName}</span>
        <span className="text-base text-[#64748B]">/</span>
        <span className="text-sm text-[#94A3B8]">{workspace}</span>
      </div>

      {/* Right: Actions */}
      <div className="flex items-center gap-4">
        {/* Notifications */}
        <button
          className="relative flex h-10 w-10 items-center justify-center rounded-lg text-[#94A3B8] transition-colors hover:bg-[#1E293B] hover:text-[#F8FAFC]"
          aria-label="Notifications"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.67" strokeLinecap="round" strokeLinejoin="round">
            <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
            <path d="M13.73 21a2 2 0 0 1-3.46 0" />
          </svg>
          {notificationCount > 0 && (
            <span className="absolute right-1.5 top-1.5 flex h-4 w-4 items-center justify-center rounded-full bg-[#EF4444] text-[9px] font-bold text-white">
              {notificationCount}
            </span>
          )}
        </button>

        {/* Date Range Picker */}
        <div className="flex items-center rounded-lg bg-[#1E293B] p-1">
          {(
            [
              { key: "7d", label: "Last 7 days" },
              { key: "30d", label: "Last 30 days" },
              { key: "custom", label: "Custom" },
            ] as const
          ).map(({ key, label }) => (
            <button
              key={key}
              onClick={() => setDateRange(key)}
              className={`rounded-md px-3 py-1.5 text-xs font-medium transition-colors ${
                dateRange === key
                  ? "bg-[#334155] text-white"
                  : "text-[#CBD5E1] hover:text-white"
              }`}
            >
              {label}
            </button>
          ))}
        </div>

        {/* Export */}
        <button
          className="flex h-9 w-9 items-center justify-center rounded-lg text-[#94A3B8] transition-colors hover:bg-[#1E293B] hover:text-[#F8FAFC]"
          aria-label="Export"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.67" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
            <polyline points="7 10 12 15 17 10" />
            <line x1="12" y1="15" x2="12" y2="3" />
          </svg>
        </button>
      </div>
    </header>
  );
}
