"use client";

import {
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Area,
  AreaChart,
} from "recharts";
import type { TimeseriesPoint } from "@/lib/hooks/useAnalytics";

interface SpendLineChartProps {
  data: TimeseriesPoint[];
  loading: boolean;
}

function fmtUsd(v: string | number) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 2,
    maximumFractionDigits: 4,
  }).format(Number(v));
}

interface TooltipPayload {
  value: string | number;
  name: string;
}

function CustomTooltip({
  active,
  payload,
  label,
}: {
  active?: boolean;
  payload?: TooltipPayload[];
  label?: string;
}) {
  if (!active || !payload?.length) return null;
  const spend = payload[0]?.value;
  const requests = payload[1]?.value;
  return (
    <div
      className="rounded-lg px-3 py-2 text-xs shadow-lg"
      style={{ background: "#1E293B", border: "1px solid #334155" }}
    >
      <p className="mb-1 font-medium text-[#F8FAFC]">{label}</p>
      <p className="text-[#60A5FA]">Spend: {fmtUsd(spend ?? 0)}</p>
      {requests !== undefined && (
        <p className="text-[#94A3B8]">
          Requests: {Number(requests).toLocaleString()}
        </p>
      )}
    </div>
  );
}

export function SpendLineChart({ data, loading }: SpendLineChartProps) {
  if (loading) {
    return (
      <div className="h-64 animate-pulse rounded-xl" style={{ background: "#0F172A" }} />
    );
  }

  if (!data.length) {
    return (
      <div className="flex h-64 items-center justify-center rounded-xl text-sm text-[#64748B]"
        style={{ background: "#0F172A" }}
      >
        No data for this period
      </div>
    );
  }

  const chartData = data.map((p) => ({
    date: new Intl.DateTimeFormat("en-US", { month: "short", day: "numeric" }).format(
      new Date(p.date)
    ),
    spend: Number(p.spend),
    requests: p.requests,
  }));

  return (
    <ResponsiveContainer width="100%" height={256}>
      <AreaChart data={chartData} margin={{ top: 4, right: 4, bottom: 0, left: 0 }}>
        <defs>
          <linearGradient id="spendGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.3} />
            <stop offset="95%" stopColor="#3B82F6" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
        <XAxis
          dataKey="date"
          tick={{ fill: "#64748B", fontSize: 11 }}
          axisLine={false}
          tickLine={false}
        />
        <YAxis
          tick={{ fill: "#64748B", fontSize: 11 }}
          axisLine={false}
          tickLine={false}
          tickFormatter={(v) => `$${v}`}
          width={48}
        />
        <Tooltip content={<CustomTooltip />} />
        <Area
          type="monotone"
          dataKey="spend"
          stroke="#3B82F6"
          strokeWidth={2}
          fill="url(#spendGradient)"
          dot={false}
          activeDot={{ r: 4, fill: "#3B82F6" }}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}
