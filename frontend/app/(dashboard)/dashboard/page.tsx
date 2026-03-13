"use client";

import { useState } from "react";
import { TrendingUp, TrendingDown, Activity, Zap } from "lucide-react";

import { KpiCard } from "@/components/dashboard/KpiCard";
import { SpendChart } from "@/components/dashboard/SpendChart";
import { ModelBreakdown } from "@/components/dashboard/ModelBreakdown";
import { ActivityTable } from "@/components/dashboard/ActivityTable";
import {
  useSummary,
  useSpendOverTime,
  useSpendByModel,
  useActivity,
} from "@/lib/hooks/useDashboard";

type DateRange = "7" | "30" | "90";

function fmtUsd(v: number) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 2,
    maximumFractionDigits: 4,
  }).format(v);
}

function fmtNum(v: number) {
  return new Intl.NumberFormat("en-US").format(v);
}

function fmtTokens(v: number) {
  if (v >= 1_000_000) return `${(v / 1_000_000).toFixed(1)}M`;
  if (v >= 1_000) return `${(v / 1_000).toFixed(1)}k`;
  return String(v);
}

export default function DashboardPage() {
  const [days, setDays] = useState<DateRange>("30");
  const [activityPage, setActivityPage] = useState(1);

  const daysNum = parseInt(days);

  const { data: summary, isLoading: loadingSummary } = useSummary(daysNum);
  const { data: spendOverTime, isLoading: loadingChart } = useSpendOverTime(daysNum);
  const { data: byModel, isLoading: loadingModel } = useSpendByModel(daysNum);
  const { data: activity, isLoading: loadingActivity } = useActivity(activityPage);

  return (
    <div className="space-y-8">
      {/* Page header + date range */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-[#F8FAFC]">Dashboard</h1>
          <p className="mt-1 text-sm text-[#94A3B8]">
            Monitor your LLM usage and costs in real time.
          </p>
        </div>

        {/* Date range picker */}
        <div className="flex items-center rounded-lg bg-[#0F172A] p-1">
          {(
            [
              { key: "7", label: "Last 7 days" },
              { key: "30", label: "Last 30 days" },
              { key: "90", label: "Last 90 days" },
            ] as const
          ).map(({ key, label }) => (
            <button
              key={key}
              onClick={() => {
                setDays(key);
                setActivityPage(1);
              }}
              className={`rounded-md px-3 py-1.5 text-xs font-medium transition-colors ${
                days === key
                  ? "bg-[#334155] text-white"
                  : "text-[#CBD5E1] hover:text-white"
              }`}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* Row 1 — KPI Cards */}
      <div className="flex gap-6">
        <KpiCard
          label="Total Spend"
          value={summary ? fmtUsd(summary.total_spend_usd) : "—"}
          change={summary?.spend_change_pct}
          loading={loadingSummary}
          icon={
            summary?.spend_change_pct && summary.spend_change_pct > 0 ? (
              <TrendingUp size={14} className="text-[#EF4444]" />
            ) : (
              <TrendingDown size={14} className="text-[#10B981]" />
            )
          }
        />
        <KpiCard
          label="Total Requests"
          value={summary ? fmtNum(summary.request_count) : "—"}
          change={summary?.request_change_pct}
          loading={loadingSummary}
          icon={<Activity size={14} className="text-[#3B82F6]" />}
        />
        <KpiCard
          label="Avg Cost / Request"
          value={summary ? fmtUsd(summary.avg_cost_per_request) : "—"}
          change={
            summary?.spend_change_pct != null && summary?.request_change_pct != null
              ? +(summary.spend_change_pct - summary.request_change_pct).toFixed(1)
              : null
          }
          loading={loadingSummary}
          icon={<Zap size={14} className="text-[#F59E0B]" />}
        />
        <KpiCard
          label="Total Tokens"
          value={summary ? fmtTokens(summary.total_tokens) : "—"}
          loading={loadingSummary}
        />
      </div>

      {/* Row 2 — Charts */}
      <div className="flex gap-6">
        {/* Area chart — takes ~57% width */}
        <div className="flex-[3]">
          <SpendChart data={spendOverTime ?? []} loading={loadingChart} />
        </div>

        {/* Model breakdown — takes ~43% width */}
        <div className="flex-[2]">
          <ModelBreakdown data={byModel ?? []} loading={loadingModel} />
        </div>
      </div>

      {/* Row 3 — Activity table */}
      <ActivityTable
        items={activity?.items ?? []}
        total={activity?.total ?? 0}
        page={activityPage}
        pageSize={10}
        loading={loadingActivity}
        onPageChange={setActivityPage}
      />
    </div>
  );
}
