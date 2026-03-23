"use client";

import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { DailySpend } from "@/lib/hooks/useDashboard";

interface SpendChartProps {
  data: DailySpend[];
  loading?: boolean;
}

function fmt(date: string) {
  return new Date(date).toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

function fmtUsd(v: number | string) {
  return `$${Number(v).toFixed(2)}`;
}

export function SpendChart({ data, loading }: SpendChartProps) {
  return (
    <div className="flex flex-col gap-6 rounded-xl bg-[#1E293B] p-6">
      <div className="flex items-center justify-between">
        <h3 className="text-base font-semibold text-[#F8FAFC]">Daily Spend</h3>
        {data.length > 0 && (
          <span className="text-xs text-[#64748B]">
            Total: {fmtUsd(data.reduce((s, d) => s + Number(d.spend_usd), 0))}
          </span>
        )}
      </div>

      {loading ? (
        <div className="h-64 animate-pulse rounded-lg bg-[#334155]" />
      ) : data.length === 0 ? (
        <EmptyState />
      ) : (
        <ResponsiveContainer width="100%" height={256}>
          <AreaChart data={data} margin={{ top: 4, right: 4, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="spendGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#3B82F6" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#1E293B" vertical={false} />
            <XAxis
              dataKey="date"
              tickFormatter={fmt}
              tick={{ fill: "#64748B", fontSize: 11 }}
              axisLine={false}
              tickLine={false}
            />
            <YAxis
              tickFormatter={fmtUsd}
              tick={{ fill: "#64748B", fontSize: 11 }}
              axisLine={false}
              tickLine={false}
              width={56}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "#0F172A",
                border: "1px solid #334155",
                borderRadius: 8,
                color: "#F8FAFC",
                fontSize: 12,
              }}
              // eslint-disable-next-line @typescript-eslint/no-explicit-any
              formatter={(v: any) => [fmtUsd(Number(v)), "Spend"] as [string, string]}
              // eslint-disable-next-line @typescript-eslint/no-explicit-any
              labelFormatter={(label: any) => fmt(String(label))}
            />
            <Area
              type="monotone"
              dataKey="spend_usd"
              stroke="#3B82F6"
              strokeWidth={2}
              fill="url(#spendGradient)"
              dot={false}
              activeDot={{ r: 4, fill: "#3B82F6" }}
            />
          </AreaChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}

function EmptyState() {
  return (
    <div className="flex h-64 items-center justify-center rounded-lg border border-dashed border-[#334155]">
      <p className="text-sm text-[#64748B]">No data for this period</p>
    </div>
  );
}
