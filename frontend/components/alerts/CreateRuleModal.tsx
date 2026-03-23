"use client";

import { useState } from "react";
import { X } from "lucide-react";
import { createAlertRule, type AlertRuleType, type AlertScope } from "@/lib/hooks/useAlerts";

interface Props {
  onClose: () => void;
  onCreated: () => void;
}

const RULE_TYPES: { value: AlertRuleType; label: string; desc: string }[] = [
  { value: "budget_soft", label: "Soft Budget", desc: "Warning when spend reaches 80% of threshold" },
  { value: "budget_hard", label: "Hard Budget", desc: "Block requests when spend hits threshold" },
  { value: "anomaly", label: "Anomaly Detection", desc: "Alert when last-hour spend exceeds N× the 7-day average" },
  { value: "circuit_breaker", label: "Circuit Breaker", desc: "Auto-block all requests when 5-min spend exceeds threshold" },
];

const SCOPES: { value: AlertScope; label: string }[] = [
  { value: "daily", label: "Daily" },
  { value: "monthly", label: "Monthly" },
  { value: "hourly", label: "Hourly" },
];

export function CreateRuleModal({ onClose, onCreated }: Props) {
  const [type, setType] = useState<AlertRuleType>("budget_soft");
  const [scope, setScope] = useState<AlertScope>("daily");
  const [threshold, setThreshold] = useState("");
  const [multiplier, setMultiplier] = useState("3.0");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const needsThreshold = type !== "anomaly";
  const needsMultiplier = type === "anomaly";

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      await createAlertRule({
        type,
        scope,
        ...(needsThreshold ? { threshold_value: threshold } : {}),
        ...(needsMultiplier ? { anomaly_multiplier: multiplier } : {}),
      });
      onCreated();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create rule");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
      <div
        className="w-full max-w-md rounded-xl shadow-2xl"
        style={{ background: "#1E293B", border: "1px solid #334155" }}
      >
        {/* Header */}
        <div className="flex items-center justify-between border-b border-[#334155] px-6 py-4">
          <h2 className="text-base font-semibold text-[#F8FAFC]">New Alert Rule</h2>
          <button onClick={onClose} className="text-[#64748B] hover:text-[#F8FAFC] transition-colors">
            <X size={18} />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-5 p-6">
          {/* Rule type */}
          <div className="space-y-2">
            <label className="text-xs font-medium text-[#94A3B8]">Rule Type</label>
            <div className="grid grid-cols-2 gap-2">
              {RULE_TYPES.map((rt) => (
                <button
                  key={rt.value}
                  type="button"
                  onClick={() => setType(rt.value)}
                  className="rounded-lg p-3 text-left transition-colors"
                  style={{
                    background: type === rt.value ? "rgba(59,130,246,0.15)" : "#0F172A",
                    border: `1px solid ${type === rt.value ? "#3B82F6" : "#334155"}`,
                  }}
                >
                  <p className="text-xs font-semibold text-[#F8FAFC]">{rt.label}</p>
                  <p className="mt-0.5 text-[10px] text-[#64748B]">{rt.desc}</p>
                </button>
              ))}
            </div>
          </div>

          {/* Scope */}
          <div className="space-y-2">
            <label className="text-xs font-medium text-[#94A3B8]">Scope</label>
            <div className="flex gap-2">
              {SCOPES.map((s) => (
                <button
                  key={s.value}
                  type="button"
                  onClick={() => setScope(s.value)}
                  className="flex-1 rounded-lg py-2 text-xs font-medium transition-colors"
                  style={{
                    background: scope === s.value ? "#334155" : "#0F172A",
                    border: `1px solid ${scope === s.value ? "#3B82F6" : "#334155"}`,
                    color: scope === s.value ? "#F8FAFC" : "#94A3B8",
                  }}
                >
                  {s.label}
                </button>
              ))}
            </div>
          </div>

          {/* Threshold */}
          {needsThreshold && (
            <div className="space-y-2">
              <label className="text-xs font-medium text-[#94A3B8]">
                Threshold (USD)
              </label>
              <div className="relative">
                <span className="absolute left-3 top-1/2 -translate-y-1/2 text-sm text-[#64748B]">$</span>
                <input
                  type="number"
                  min="0"
                  step="0.01"
                  required
                  value={threshold}
                  onChange={(e) => setThreshold(e.target.value)}
                  placeholder="10.00"
                  className="w-full rounded-lg py-2 pl-7 pr-3 text-sm text-[#F8FAFC] outline-none transition-colors"
                  style={{ background: "#0F172A", border: "1px solid #334155" }}
                />
              </div>
            </div>
          )}

          {/* Anomaly multiplier */}
          {needsMultiplier && (
            <div className="space-y-2">
              <label className="text-xs font-medium text-[#94A3B8]">
                Multiplier (× 7-day avg)
              </label>
              <input
                type="number"
                min="1"
                step="0.5"
                required
                value={multiplier}
                onChange={(e) => setMultiplier(e.target.value)}
                placeholder="3.0"
                className="w-full rounded-lg px-3 py-2 text-sm text-[#F8FAFC] outline-none"
                style={{ background: "#0F172A", border: "1px solid #334155" }}
              />
              <p className="text-[10px] text-[#64748B]">
                Alert fires when last-hour spend &gt; {multiplier}× the 7-day hourly average
              </p>
            </div>
          )}

          {error && (
            <p className="rounded-lg bg-red-500/10 px-3 py-2 text-xs text-red-400">{error}</p>
          )}

          {/* Actions */}
          <div className="flex gap-3 pt-1">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 rounded-lg py-2 text-sm font-medium text-[#94A3B8] transition-colors hover:text-[#F8FAFC]"
              style={{ background: "#0F172A", border: "1px solid #334155" }}
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={saving}
              className="flex-1 rounded-lg py-2 text-sm font-medium text-white transition-colors"
              style={{ background: saving ? "#334155" : "#3B82F6", cursor: saving ? "not-allowed" : "pointer" }}
            >
              {saving ? "Creating…" : "Create Rule"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
