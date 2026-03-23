"use client";

interface BudgetTrackerProps {
  spent: number;
  budget: number | null;
}

function fmtUsd(v: number) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(v);
}

export function BudgetTracker({ spent, budget }: BudgetTrackerProps) {
  if (!budget) {
    return (
      <div
        className="rounded-xl px-6 py-4"
        style={{ background: "#1E293B", border: "1px solid #334155" }}
      >
        <p className="text-xs font-medium uppercase tracking-wider text-[#64748B]">
          Budget
        </p>
        <p className="mt-1 text-sm text-[#94A3B8]">No budget set</p>
      </div>
    );
  }

  const pct = Math.min((spent / budget) * 100, 100);
  const color = pct >= 85 ? "#EF4444" : pct >= 60 ? "#F59E0B" : "#10B981";

  return (
    <div
      className="rounded-xl px-6 py-4"
      style={{ background: "#1E293B", border: "1px solid #334155" }}
    >
      <div className="mb-3 flex items-center justify-between">
        <p className="text-xs font-medium uppercase tracking-wider text-[#64748B]">
          Budget
        </p>
        <p className="text-xs text-[#94A3B8]">
          {fmtUsd(spent)} / {fmtUsd(budget)} &nbsp;·&nbsp;
          <span style={{ color }}>{pct.toFixed(0)}%</span>
        </p>
      </div>
      <div className="h-2 w-full overflow-hidden rounded-full bg-[#334155]">
        <div
          className="h-full rounded-full transition-all"
          style={{ width: `${pct}%`, background: color }}
        />
      </div>
    </div>
  );
}
