"use client";

import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from "recharts";
import type { ModelUsage } from "@/lib/hooks/useAnalytics";

interface ModelDonutChartProps {
  data: ModelUsage[];
  loading: boolean;
}

const COLORS = [
  "#3B82F6",
  "#10B981",
  "#F59E0B",
  "#A855F7",
  "#EF4444",
  "#06B6D4",
  "#F97316",
  "#84CC16",
];

function fmtUsd(v: string | number) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 2,
    maximumFractionDigits: 4,
  }).format(Number(v));
}

interface TooltipPayload {
  payload: ModelUsage & { fill: string };
  name: string;
  value: number;
}

function CustomTooltip({
  active,
  payload,
}: {
  active?: boolean;
  payload?: TooltipPayload[];
}) {
  if (!active || !payload?.length) return null;
  const item = payload[0]?.payload;
  return (
    <div
      className="rounded-lg px-3 py-2 text-xs shadow-lg"
      style={{ background: "#1E293B", border: "1px solid #334155" }}
    >
      <p className="font-medium text-[#F8FAFC]">{item?.model_name}</p>
      <p className="text-[#60A5FA]">{fmtUsd(item?.spend ?? 0)}</p>
      <p className="text-[#94A3B8]">{item?.pct_of_total?.toFixed(1)}%</p>
    </div>
  );
}

export function ModelDonutChart({ data, loading }: ModelDonutChartProps) {
  if (loading) {
    return (
      <div className="h-64 animate-pulse rounded-xl" style={{ background: "#0F172A" }} />
    );
  }

  if (!data.length) {
    return (
      <div
        className="flex h-64 items-center justify-center rounded-xl text-sm text-[#64748B]"
        style={{ background: "#0F172A" }}
      >
        No model data yet
      </div>
    );
  }

  const chartData = data.map((m) => ({
    ...m,
    value: Number(m.spend),
  }));

  return (
    <div className="h-64">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={chartData}
            cx="50%"
            cy="45%"
            innerRadius={56}
            outerRadius={88}
            dataKey="value"
            paddingAngle={2}
          >
            {chartData.map((_, i) => (
              <Cell key={i} fill={COLORS[i % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip content={<CustomTooltip />} />
          <Legend
            formatter={(value) => (
              <span style={{ color: "#94A3B8", fontSize: 11 }}>{value}</span>
            )}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
