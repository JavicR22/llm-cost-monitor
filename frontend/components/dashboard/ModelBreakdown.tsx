"use client";

import { SpendByModel } from "@/lib/hooks/useDashboard";

interface ModelBreakdownProps {
  data: SpendByModel[];
  loading?: boolean;
}

const MODEL_COLORS = [
  "#3B82F6", // blue
  "#8B5CF6", // purple
  "#10B981", // green
  "#F59E0B", // amber
  "#EF4444", // red
  "#06B6D4", // cyan
];

function fmtUsd(v: number | string) {
  const n = Number(v);
  if (n >= 1000) return `$${(n / 1000).toFixed(1)}k`;
  return `$${n.toFixed(2)}`;
}

export function ModelBreakdown({ data, loading }: ModelBreakdownProps) {
  return (
    <div className="flex flex-col gap-4 rounded-xl bg-[#1E293B] p-6">
      <h3 className="text-base font-semibold text-[#F8FAFC]">Spend by Model</h3>

      {loading ? (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-8 animate-pulse rounded bg-[#334155]" />
          ))}
        </div>
      ) : data.length === 0 ? (
        <p className="text-sm text-[#64748B]">No data for this period</p>
      ) : (
        <div className="space-y-3">
          {data.map((model, i) => (
            <div key={model.model_name} className="space-y-1">
              <div className="flex items-center justify-between text-xs">
                <span className="font-medium text-[#F8FAFC]">{model.display_name}</span>
                <div className="flex items-center gap-2 text-[#94A3B8]">
                  <span>{Number(model.pct_of_total).toFixed(1)}%</span>
                  <span className="font-semibold text-[#F8FAFC]">{fmtUsd(model.spend_usd)}</span>
                </div>
              </div>
              {/* Bar */}
              <div className="h-1.5 w-full overflow-hidden rounded-full bg-[#0F172A]">
                <div
                  className="h-full rounded-full transition-all duration-500"
                  style={{
                    width: `${model.pct_of_total}%`,
                    backgroundColor: MODEL_COLORS[i % MODEL_COLORS.length],
                  }}
                />
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
