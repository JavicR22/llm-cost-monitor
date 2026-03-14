"use client";

import { useState } from "react";
import { Plus, Trash2 } from "lucide-react";
import { useAlertRules, toggleAlertRule, deleteAlertRule, type AlertRule } from "@/lib/hooks/useAlerts";
import { CreateRuleModal } from "./CreateRuleModal";

const TYPE_LABELS: Record<string, string> = {
  budget_soft: "Soft Budget",
  budget_hard: "Hard Budget",
  anomaly: "Anomaly",
  circuit_breaker: "Circuit Breaker",
};

const TYPE_COLORS: Record<string, string> = {
  budget_soft: "#F59E0B",
  budget_hard: "#EF4444",
  anomaly: "#3B82F6",
  circuit_breaker: "#8B5CF6",
};

function RuleRow({
  rule,
  onToggle,
  onDelete,
}: {
  rule: AlertRule;
  onToggle: (id: string, active: boolean) => Promise<void>;
  onDelete: (id: string) => Promise<void>;
}) {
  const [busy, setBusy] = useState(false);

  async function handleToggle() {
    setBusy(true);
    try { await onToggle(rule.id, !rule.is_active); } finally { setBusy(false); }
  }

  async function handleDelete() {
    if (!confirm("Delete this alert rule?")) return;
    setBusy(true);
    try { await onDelete(rule.id); } finally { setBusy(false); }
  }

  const color = TYPE_COLORS[rule.type] ?? "#94A3B8";

  return (
    <div
      className="flex items-center gap-4 rounded-lg px-4 py-3 transition-colors"
      style={{ background: "#0F172A", border: "1px solid #334155" }}
    >
      {/* Type badge */}
      <span
        className="shrink-0 rounded px-2 py-0.5 text-[11px] font-semibold"
        style={{ background: `${color}20`, color }}
      >
        {TYPE_LABELS[rule.type] ?? rule.type}
      </span>

      {/* Info */}
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm text-[#F8FAFC]">
          {rule.scope.charAt(0).toUpperCase() + rule.scope.slice(1)} •{" "}
          {rule.threshold_value != null
            ? `$${parseFloat(rule.threshold_value).toFixed(2)}`
            : `${rule.anomaly_multiplier}× avg`}
        </p>
      </div>

      {/* Toggle */}
      <button
        onClick={handleToggle}
        disabled={busy}
        title={rule.is_active ? "Disable" : "Enable"}
        className="relative h-5 w-9 shrink-0 rounded-full transition-colors"
        style={{
          background: rule.is_active ? "#3B82F6" : "#334155",
          cursor: busy ? "not-allowed" : "pointer",
        }}
      >
        <span
          className="absolute top-0.5 h-4 w-4 rounded-full bg-white shadow transition-transform"
          style={{ transform: rule.is_active ? "translateX(18px)" : "translateX(2px)" }}
        />
      </button>

      {/* Delete */}
      <button
        onClick={handleDelete}
        disabled={busy}
        className="shrink-0 rounded p-1 text-[#64748B] transition-colors hover:bg-red-500/10 hover:text-red-400"
      >
        <Trash2 size={14} />
      </button>
    </div>
  );
}

export function AlertRulesList() {
  const { data: rules, isLoading, mutate } = useAlertRules();
  const [showModal, setShowModal] = useState(false);

  async function handleToggle(id: string, active: boolean) {
    await toggleAlertRule(id, active);
    await mutate();
  }

  async function handleDelete(id: string) {
    await deleteAlertRule(id);
    await mutate();
  }

  return (
    <div
      className="flex flex-col rounded-xl"
      style={{ background: "#1E293B", border: "1px solid #334155" }}
    >
      {/* Header */}
      <div className="flex items-center justify-between border-b border-[#334155] px-5 py-4">
        <div>
          <h2 className="text-sm font-semibold text-[#F8FAFC]">Alert Rules</h2>
          <p className="text-xs text-[#64748B]">{rules?.length ?? 0} configured</p>
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium text-white transition-colors hover:bg-[#2563EB]"
          style={{ background: "#3B82F6" }}
        >
          <Plus size={13} />
          New Rule
        </button>
      </div>

      {/* List */}
      <div className="flex flex-col gap-2 p-4">
        {isLoading ? (
          Array.from({ length: 3 }).map((_, i) => (
            <div
              key={i}
              className="h-12 animate-pulse rounded-lg"
              style={{ background: "#0F172A" }}
            />
          ))
        ) : rules?.length === 0 ? (
          <p className="py-8 text-center text-sm text-[#64748B]">
            No alert rules configured yet.
          </p>
        ) : (
          rules?.map((rule) => (
            <RuleRow
              key={rule.id}
              rule={rule}
              onToggle={handleToggle}
              onDelete={handleDelete}
            />
          ))
        )}
      </div>

      {showModal && (
        <CreateRuleModal
          onClose={() => setShowModal(false)}
          onCreated={async () => {
            setShowModal(false);
            await mutate();
          }}
        />
      )}
    </div>
  );
}
