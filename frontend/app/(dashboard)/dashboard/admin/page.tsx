"use client";

import { useState } from "react";
import Link from "next/link";
import { TrendingUp, TrendingDown, Users, FolderOpen, Activity, DollarSign, ArrowRight } from "lucide-react";
import {
  useOverview,
  useProjectsAnalytics,
  useTimeseries,
  useModelsUsage,
  type Range,
} from "@/lib/hooks/useAnalytics";
import { RoleGuard } from "@/components/auth/RoleGuard";
import { RangeSelector } from "@/components/analytics/RangeSelector";
import { SpendLineChart } from "@/components/analytics/SpendLineChart";
import { ModelDonutChart } from "@/components/analytics/ModelDonutChart";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function fmtUsd(v: string | number) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(Number(v));
}

function fmtNum(v: number | string) {
  return new Intl.NumberFormat("en-US").format(Number(v));
}

// ---------------------------------------------------------------------------
// KPI Card
// ---------------------------------------------------------------------------

function AdminKpiCard({
  label,
  value,
  trend,
  icon,
  loading,
}: {
  label: string;
  value: string;
  trend?: number | null;
  icon: React.ReactNode;
  loading: boolean;
}) {
  const isUp = trend !== null && trend !== undefined && trend > 0;
  const isDown = trend !== null && trend !== undefined && trend < 0;

  return (
    <div
      className="flex flex-1 flex-col gap-4 rounded-xl p-5"
      style={{ background: "#1E293B", border: "1px solid #334155" }}
    >
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-[#94A3B8]">{label}</span>
        <div
          className="flex h-7 w-7 items-center justify-center rounded-full"
          style={{ background: "rgba(59,130,246,0.15)" }}
        >
          {icon}
        </div>
      </div>
      <div className="flex items-end gap-2">
        {loading ? (
          <div className="h-8 w-32 animate-pulse rounded bg-[#334155]" />
        ) : (
          <span className="text-2xl font-bold text-[#F8FAFC]">{value}</span>
        )}
        {!loading && trend !== null && trend !== undefined && (
          <span
            className="mb-0.5 flex items-center gap-0.5 text-xs font-medium"
            style={{ color: isUp ? "#F87171" : isDown ? "#34D399" : "#64748B" }}
          >
            {isUp ? <TrendingUp size={12} /> : isDown ? <TrendingDown size={12} /> : null}
            {isUp ? "+" : ""}
            {trend.toFixed(1)}%
          </span>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Budget bar for projects table
// ---------------------------------------------------------------------------

function MiniProgressBar({ pct }: { pct: number }) {
  const color = pct >= 85 ? "#EF4444" : pct >= 60 ? "#F59E0B" : "#10B981";
  return (
    <div className="h-1.5 w-full overflow-hidden rounded-full bg-[#334155]">
      <div
        className="h-full rounded-full transition-all"
        style={{ width: `${Math.min(pct, 100)}%`, background: color }}
      />
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------

export default function AdminDashboardPage() {
  const [range, setRange] = useState<Range>("30d");

  const { data: overview, isLoading: loadingOverview } = useOverview(range);
  const { data: projects, isLoading: loadingProjects } = useProjectsAnalytics(range);
  const { data: timeseries, isLoading: loadingTs } = useTimeseries(range);
  const { data: models, isLoading: loadingModels } = useModelsUsage(range);

  return (
    <RoleGuard allowedRoles={["owner", "admin", "project_leader"]}>
      <div className="space-y-8">
        {/* Header */}
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-[#F8FAFC]">
              Analytics
            </h1>
            <p className="mt-1 text-sm text-[#94A3B8]">
              Org-wide LLM spend and usage by project, team, and model.
            </p>
          </div>
          <RangeSelector value={range} onChange={setRange} />
        </div>

        {/* KPI row */}
        <div className="flex gap-4">
          <AdminKpiCard
            label="Total Spend"
            value={overview ? fmtUsd(overview.total_spend) : "—"}
            trend={overview?.spend_trend_pct ?? null}
            icon={<DollarSign size={14} className="text-[#3B82F6]" />}
            loading={loadingOverview}
          />
          <AdminKpiCard
            label="Total Requests"
            value={overview ? fmtNum(overview.total_requests) : "—"}
            icon={<Activity size={14} className="text-[#10B981]" />}
            loading={loadingOverview}
          />
          <AdminKpiCard
            label="Active Developers"
            value={overview ? fmtNum(overview.active_developers) : "—"}
            icon={<Users size={14} className="text-[#F59E0B]" />}
            loading={loadingOverview}
          />
          <AdminKpiCard
            label="Active Projects"
            value={overview ? fmtNum(overview.active_projects) : "—"}
            icon={<FolderOpen size={14} className="text-[#A855F7]" />}
            loading={loadingOverview}
          />
        </div>

        {/* Charts row */}
        <div className="flex gap-6">
          {/* Spend timeline — 2/3 */}
          <div
            className="flex-[2] rounded-xl p-6"
            style={{ background: "#1E293B", border: "1px solid #334155" }}
          >
            <h3 className="mb-4 text-sm font-semibold text-[#F8FAFC]">
              Daily Spend
            </h3>
            <SpendLineChart
              data={timeseries?.series ?? []}
              loading={loadingTs}
            />
          </div>

          {/* Model breakdown — 1/3 */}
          <div
            className="flex-[1] rounded-xl p-6"
            style={{ background: "#1E293B", border: "1px solid #334155" }}
          >
            <h3 className="mb-4 text-sm font-semibold text-[#F8FAFC]">
              Spend by Model
            </h3>
            <ModelDonutChart data={models ?? []} loading={loadingModels} />
          </div>
        </div>

        {/* Projects table */}
        <div
          className="overflow-hidden rounded-xl"
          style={{ background: "#1E293B", border: "1px solid #334155" }}
        >
          <div className="border-b border-[#0F172A] bg-[#0F172A] px-6 py-4">
            <h3 className="text-base font-semibold text-[#F8FAFC]">Projects</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-[#0F172A] bg-[#0F172A]">
                  {["Name", "Spend", "Requests", "Teams", "Developers", "Budget", ""].map(
                    (col) => (
                      <th
                        key={col}
                        className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-[#64748B]"
                      >
                        {col}
                      </th>
                    )
                  )}
                </tr>
              </thead>
              <tbody>
                {loadingProjects
                  ? Array.from({ length: 4 }).map((_, i) => (
                      <tr key={i} className={i % 2 === 1 ? "bg-[#0F172A]" : ""}>
                        {Array.from({ length: 7 }).map((_, j) => (
                          <td key={j} className="px-6 py-4">
                            <div className="h-4 animate-pulse rounded bg-[#334155]" />
                          </td>
                        ))}
                      </tr>
                    ))
                  : (projects ?? []).map((p, i) => (
                      <tr
                        key={p.id}
                        className={`transition-colors hover:bg-[#334155]/20 ${
                          i % 2 === 1 ? "bg-[#0F172A]" : ""
                        }`}
                      >
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-2">
                            <FolderOpen size={14} className="shrink-0 text-[#3B82F6]" />
                            <span className="font-medium text-[#F8FAFC]">{p.name}</span>
                          </div>
                        </td>
                        <td className="px-6 py-4 font-mono text-[#F8FAFC]">
                          {fmtUsd(p.spend_30d)}
                        </td>
                        <td className="px-6 py-4 text-[#94A3B8]">
                          {fmtNum(p.requests_30d)}
                        </td>
                        <td className="px-6 py-4 text-[#94A3B8]">{p.teams_count}</td>
                        <td className="px-6 py-4 text-[#94A3B8]">{p.members_count}</td>
                        <td className="min-w-[140px] px-6 py-4">
                          {p.budget ? (
                            <div className="space-y-1">
                              <MiniProgressBar pct={p.budget_used_pct} />
                              <p className="text-xs text-[#64748B]">
                                {p.budget_used_pct.toFixed(0)}% of {fmtUsd(p.budget)}
                              </p>
                            </div>
                          ) : (
                            <span className="text-xs text-[#64748B]">No limit</span>
                          )}
                        </td>
                        <td className="px-6 py-4 text-right">
                          <Link
                            href={`/dashboard/admin/projects/${p.id}`}
                            className="inline-flex items-center gap-1 rounded-md px-3 py-1 text-xs font-medium text-[#60A5FA] transition-colors hover:bg-[#3B82F6]/10"
                          >
                            View
                            <ArrowRight size={12} />
                          </Link>
                        </td>
                      </tr>
                    ))}
                {!loadingProjects && (projects ?? []).length === 0 && (
                  <tr>
                    <td
                      colSpan={7}
                      className="px-6 py-12 text-center text-sm text-[#64748B]"
                    >
                      No projects found for this period.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </RoleGuard>
  );
}
