"use client";

import { useState } from "react";
import { ShieldAlert, ShieldCheck, Unlock } from "lucide-react";
import { useCircuitBreaker, unlockCircuitBreaker } from "@/lib/hooks/useAlerts";

export function CircuitBreakerPanel() {
  const { data, isLoading, mutate } = useCircuitBreaker();
  const [unlocking, setUnlocking] = useState(false);

  async function handleUnlock() {
    setUnlocking(true);
    try {
      await unlockCircuitBreaker();
      await mutate();
    } finally {
      setUnlocking(false);
    }
  }

  const isOpen = data?.is_open ?? false;

  return (
    <div
      className="flex items-center justify-between rounded-xl p-5"
      style={{
        background: isOpen ? "rgba(239,68,68,0.08)" : "rgba(16,185,129,0.08)",
        border: `1px solid ${isOpen ? "#ef444440" : "#10b98140"}`,
      }}
    >
      <div className="flex items-center gap-4">
        <div
          className="flex h-11 w-11 shrink-0 items-center justify-center rounded-lg"
          style={{ background: isOpen ? "rgba(239,68,68,0.15)" : "rgba(16,185,129,0.15)" }}
        >
          {isOpen ? (
            <ShieldAlert size={22} color="#ef4444" />
          ) : (
            <ShieldCheck size={22} color="#10b981" />
          )}
        </div>
        <div>
          <p className="text-sm font-semibold text-[#F8FAFC]">
            Circuit Breaker&nbsp;
            <span
              className="rounded px-1.5 py-0.5 text-[11px] font-bold"
              style={{
                background: isOpen ? "#ef444420" : "#10b98120",
                color: isOpen ? "#ef4444" : "#10b981",
              }}
            >
              {isLoading ? "…" : isOpen ? "OPEN" : "CLOSED"}
            </span>
          </p>
          <p className="mt-0.5 text-xs text-[#94A3B8]">
            {isOpen
              ? "All requests are blocked. Unlock manually when the issue is resolved."
              : "Monitoring 5-minute spend windows for anomalous activity."}
          </p>
        </div>
      </div>

      {isOpen && (
        <button
          onClick={handleUnlock}
          disabled={unlocking}
          className="flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition-colors"
          style={{
            background: unlocking ? "#334155" : "#3B82F6",
            color: "#fff",
            cursor: unlocking ? "not-allowed" : "pointer",
          }}
        >
          <Unlock size={14} />
          {unlocking ? "Unlocking…" : "Unlock"}
        </button>
      )}
    </div>
  );
}
