"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, Users, Key, BarChart3 } from "lucide-react";
import {
  useTeamsAnalytics,
  useDevelopersAnalytics,
  useTimeseries,
  useProjectsAnalytics,
  type Range,
} from "@/lib/hooks/useAnalytics";
import { RoleGuard } from "@/components/auth/RoleGuard";
import { RangeSelector } from "@/components/analytics/RangeSelector";
import { TeamsTab } from "@/components/analytics/TeamsTab";
import { DevelopersTab } from "@/components/analytics/DevelopersTab";
import { ProjectSpendChart } from "@/components/analytics/ProjectSpendChart";
import { BudgetTracker } from "@/components/analytics/BudgetTracker";

type Tab = "teams" | "developers" | "timeline";

const TABS: { key: Tab; label: string; icon: React.ElementType }[] = [
  { key: "teams", label: "Teams", icon: Users },
  { key: "developers", label: "Developers", icon: Key },
  { key: "timeline", label: "Spend Timeline", icon: BarChart3 },
];

export default function AdminProjectDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [tab, setTab] = useState<Tab>("teams");
  const [range, setRange] = useState<Range>("30d");

  const { data: allProjects } = useProjectsAnalytics(range);
  const project = (allProjects ?? []).find((p) => p.id === id);

  const { data: teams, isLoading: loadingTeams } = useTeamsAnalytics(id, range);
  const { data: developers, isLoading: loadingDevs } = useDevelopersAnalytics(id, range);
  const { data: timeseries, isLoading: loadingTs } = useTimeseries(range, id);

  const spent = Number(project?.spend_30d ?? 0);
  const budget = project?.budget ? Number(project.budget) : null;

  return (
    <RoleGuard allowedRoles={["owner", "admin", "project_leader"]}>
      <div className="space-y-8">
        {/* Back + header */}
        <div>
          <Link
            href="/dashboard/admin"
            className="mb-4 flex items-center gap-1.5 text-xs text-[#64748B] transition-colors hover:text-[#94A3B8]"
          >
            <ArrowLeft size={12} />
            Analytics
          </Link>

          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-2xl font-semibold text-[#F8FAFC]">
                {project?.name ?? "Project"}
              </h1>
              <p className="mt-1 text-sm text-[#94A3B8]">
                {project?.members_count ?? 0} developers &middot;{" "}
                {project?.teams_count ?? 0} teams
              </p>
            </div>
            <RangeSelector value={range} onChange={setRange} />
          </div>
        </div>

        {/* Budget tracker (always visible) */}
        <BudgetTracker spent={spent} budget={budget} />

        {/* Tabs */}
        <div
          className="overflow-hidden rounded-xl"
          style={{ background: "#1E293B", border: "1px solid #334155" }}
        >
          {/* Tab header */}
          <div className="flex items-center gap-1 border-b border-[#0F172A] bg-[#0F172A] px-6 py-3">
            {TABS.map(({ key, label, icon: Icon }) => (
              <button
                key={key}
                onClick={() => setTab(key)}
                className="flex items-center gap-2 rounded-md px-3 py-1.5 text-sm font-medium transition-colors"
                style={{
                  background: tab === key ? "#334155" : "transparent",
                  color: tab === key ? "#F8FAFC" : "#94A3B8",
                }}
              >
                <Icon size={14} />
                {label}
              </button>
            ))}
          </div>

          {/* Tab content */}
          {tab === "teams" && (
            <TeamsTab teams={teams ?? []} loading={loadingTeams} />
          )}
          {tab === "developers" && (
            <DevelopersTab
              developers={developers ?? []}
              loading={loadingDevs}
            />
          )}
          {tab === "timeline" && (
            <ProjectSpendChart
              data={timeseries?.series ?? []}
              loading={loadingTs}
            />
          )}
        </div>
      </div>
    </RoleGuard>
  );
}
