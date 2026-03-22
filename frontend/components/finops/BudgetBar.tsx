"use client";

interface Props {
  spent: number;
  limit: number;
}

export function BudgetBar({ spent, limit }: Props) {
  const pct = Math.min((spent / limit) * 100, 100);
  const color =
    pct >= 100
      ? "#EF4444"
      : pct >= 80
        ? "#F59E0B"
        : "#10B981";

  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-xs">
        <span className="text-[#94A3B8]">Budget used</span>
        <span style={{ color }} className="font-semibold">
          {pct.toFixed(1)}%
        </span>
      </div>
      <div className="h-1.5 w-full overflow-hidden rounded-full bg-[#334155]">
        <div
          className="h-full rounded-full transition-all duration-500"
          style={{ width: `${pct}%`, backgroundColor: color }}
        />
      </div>
      <p className="text-right text-[10px] text-[#64748B]">
        ${spent.toFixed(2)} / ${limit.toFixed(2)}
      </p>
    </div>
  );
}
