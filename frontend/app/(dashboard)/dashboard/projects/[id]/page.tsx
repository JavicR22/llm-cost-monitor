"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, Plus, Trash2, Users, Key, BarChart3 } from "lucide-react";

import {
  useProjects,
  useTeams,
  useTeamsSpend,
  useMembersSpend,
  createTeam,
  deleteTeam,
  type GroupBy,
} from "@/lib/hooks/useFinOps";
import { BudgetBar } from "@/components/finops/BudgetBar";

function todayMinus(days: number) {
  const d = new Date();
  d.setDate(d.getDate() - days);
  return d.toISOString().split("T")[0];
}

const TODAY = new Date().toISOString().split("T")[0];
const FROM_30 = todayMinus(30);

function fmtUsd(v: string | number) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 2,
    maximumFractionDigits: 4,
  }).format(Number(v));
}

type Tab = "teams" | "members";

export default function ProjectDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [tab, setTab] = useState<Tab>("teams");
  const [groupBy] = useState<GroupBy>("day");
  const [newTeamName, setNewTeamName] = useState("");
  const [creatingTeam, setCreatingTeam] = useState(false);
  const [showNewTeam, setShowNewTeam] = useState(false);

  const { data: projects } = useProjects();
  const project = (projects ?? []).find((p) => p.id === id);

  const { data: teams, mutate: mutateTeams } = useTeams(id);
  const { data: teamsSpend } = useTeamsSpend(id, FROM_30, TODAY, groupBy);
  const { data: membersSpend } = useMembersSpend(id, FROM_30, TODAY, groupBy);

  // Aggregate team spend (multiple periods → sum)
  const teamTotals = Object.fromEntries(
    Object.entries(
      (teamsSpend ?? []).reduce(
        (acc, row) => {
          const key = row.team_id;
          if (!acc[key]) acc[key] = { cost: 0, requests: 0 };
          acc[key].cost += Number(row.total_cost);
          acc[key].requests += row.requests;
          return acc;
        },
        {} as Record<string, { cost: number; requests: number }>
      )
    )
  );

  // Aggregate member spend
  const memberTotals = Object.fromEntries(
    Object.entries(
      (membersSpend ?? []).reduce(
        (acc, row) => {
          const key = row.user_id;
          if (!acc[key])
            acc[key] = { name: row.user_name, email: row.user_email, cost: 0, requests: 0 };
          acc[key].cost += Number(row.total_cost);
          acc[key].requests += row.requests;
          return acc;
        },
        {} as Record<string, { name: string; email: string; cost: number; requests: number }>
      )
    )
  );

  const totalSpent = Object.values(teamTotals).reduce((s, t) => s + t.cost, 0);
  const budgetLimit = project?.budget_limit ? Number(project.budget_limit) : null;

  async function handleCreateTeam(e: React.FormEvent) {
    e.preventDefault();
    if (!newTeamName.trim()) return;
    setCreatingTeam(true);
    try {
      await createTeam(id, { name: newTeamName.trim() });
      setNewTeamName("");
      setShowNewTeam(false);
      mutateTeams();
    } finally {
      setCreatingTeam(false);
    }
  }

  async function handleDeleteTeam(teamId: string) {
    if (!confirm("Delete this team?")) return;
    await deleteTeam(id, teamId);
    mutateTeams();
  }

  return (
    <div className="space-y-8">
      {/* Back + header */}
      <div>
        <Link
          href="/dashboard/projects"
          className="mb-4 flex items-center gap-1.5 text-xs text-[#64748B] transition-colors hover:text-[#94A3B8]"
        >
          <ArrowLeft size={12} />
          Projects
        </Link>

        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-[#F8FAFC]">
              {project?.name ?? "Project"}
            </h1>
            {project?.description && (
              <p className="mt-1 text-sm text-[#94A3B8]">{project.description}</p>
            )}
          </div>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-3 gap-4">
        {[
          {
            label: "Total Spend (30d)",
            value: fmtUsd(totalSpent),
            color: "#3B82F6",
          },
          {
            label: "Teams",
            value: String(teams?.length ?? 0),
            color: "#10B981",
          },
          {
            label: "Members",
            value: String(Object.keys(memberTotals).length),
            color: "#F59E0B",
          },
        ].map((kpi) => (
          <div
            key={kpi.label}
            className="rounded-xl bg-[#1E293B] px-6 py-5"
            style={{ border: "1px solid #334155" }}
          >
            <p className="text-xs font-medium uppercase tracking-wider text-[#64748B]">
              {kpi.label}
            </p>
            <p className="mt-2 text-2xl font-semibold" style={{ color: kpi.color }}>
              {kpi.value}
            </p>
          </div>
        ))}
      </div>

      {/* Budget bar */}
      {budgetLimit && (
        <div
          className="rounded-xl bg-[#1E293B] px-6 py-5"
          style={{ border: "1px solid #334155" }}
        >
          <p className="mb-3 text-sm font-medium text-[#F8FAFC]">Budget (30d)</p>
          <BudgetBar spent={totalSpent} limit={budgetLimit} />
        </div>
      )}

      {/* Tabs */}
      <div className="overflow-hidden rounded-xl bg-[#1E293B]" style={{ border: "1px solid #334155" }}>
        {/* Tab header */}
        <div className="flex items-center gap-1 border-b border-[#0F172A] bg-[#0F172A] px-6 py-3">
          {(
            [
              { key: "teams", label: "Teams", icon: Users },
              { key: "members", label: "Developers", icon: Key },
            ] as const
          ).map(({ key, label, icon: Icon }) => (
            <button
              key={key}
              onClick={() => setTab(key)}
              className={`flex items-center gap-2 rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
                tab === key
                  ? "bg-[#334155] text-[#F8FAFC]"
                  : "text-[#94A3B8] hover:text-[#F8FAFC]"
              }`}
            >
              <Icon size={14} />
              {label}
            </button>
          ))}
        </div>

        {/* Teams tab */}
        {tab === "teams" && (
          <div>
            <div className="flex items-center justify-between border-b border-[#0F172A] px-6 py-3">
              <span className="text-xs text-[#64748B]">{teams?.length ?? 0} teams</span>
              <button
                onClick={() => setShowNewTeam((v) => !v)}
                className="flex items-center gap-1.5 text-xs font-medium text-[#3B82F6] transition-colors hover:text-[#60A5FA]"
              >
                <Plus size={12} /> Add Team
              </button>
            </div>

            {showNewTeam && (
              <form
                onSubmit={handleCreateTeam}
                className="flex items-center gap-3 border-b border-[#0F172A] bg-[#0F172A] px-6 py-3"
              >
                <input
                  type="text"
                  value={newTeamName}
                  onChange={(e) => setNewTeamName(e.target.value)}
                  placeholder="Team name (e.g. Backend)"
                  maxLength={255}
                  className="flex-1 rounded-lg bg-[#1E293B] px-3 py-1.5 text-sm text-[#F8FAFC] placeholder-[#64748B] outline-none focus:ring-1 focus:ring-[#3B82F6]"
                  style={{ border: "1px solid #334155" }}
                />
                <button
                  type="submit"
                  disabled={creatingTeam || !newTeamName.trim()}
                  className="rounded-lg bg-[#3B82F6] px-3 py-1.5 text-xs font-medium text-white disabled:opacity-50"
                >
                  {creatingTeam ? "Creating…" : "Create"}
                </button>
                <button
                  type="button"
                  onClick={() => setShowNewTeam(false)}
                  className="text-xs text-[#64748B] hover:text-[#94A3B8]"
                >
                  Cancel
                </button>
              </form>
            )}

            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-[#0F172A] bg-[#0F172A]">
                  {["Team", "Spend (30d)", "Requests", ""].map((col) => (
                    <th
                      key={col}
                      className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-[#64748B]"
                    >
                      {col}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {(teams ?? []).map((team, i) => {
                  const spend = teamTotals[team.id];
                  return (
                    <tr
                      key={team.id}
                      className={`transition-colors hover:bg-[#334155]/20 ${i % 2 === 1 ? "bg-[#0F172A]" : ""}`}
                    >
                      <td className="px-6 py-3 font-medium text-[#F8FAFC]">{team.name}</td>
                      <td className="px-6 py-3 font-mono text-[#F8FAFC]">
                        {spend ? fmtUsd(spend.cost) : "—"}
                      </td>
                      <td className="px-6 py-3 text-[#94A3B8]">
                        {spend ? spend.requests.toLocaleString() : "—"}
                      </td>
                      <td className="px-6 py-3 text-right">
                        <button
                          onClick={() => handleDeleteTeam(team.id)}
                          className="rounded p-1 text-[#64748B] transition-colors hover:text-[#EF4444]"
                        >
                          <Trash2 size={14} />
                        </button>
                      </td>
                    </tr>
                  );
                })}
                {(teams ?? []).length === 0 && (
                  <tr>
                    <td colSpan={4} className="px-6 py-10 text-center text-sm text-[#64748B]">
                      No teams yet. Add one above.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}

        {/* Members tab */}
        {tab === "members" && (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-[#0F172A] bg-[#0F172A]">
                {["Developer", "Email", "Spend (30d)", "Requests"].map((col) => (
                  <th
                    key={col}
                    className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-[#64748B]"
                  >
                    {col}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {Object.entries(memberTotals).map(([uid, m], i) => (
                <tr
                  key={uid}
                  className={`transition-colors hover:bg-[#334155]/20 ${i % 2 === 1 ? "bg-[#0F172A]" : ""}`}
                >
                  <td className="px-6 py-3 font-medium text-[#F8FAFC]">{m.name}</td>
                  <td className="px-6 py-3 text-[#64748B]">{m.email}</td>
                  <td className="px-6 py-3 font-mono text-[#F8FAFC]">{fmtUsd(m.cost)}</td>
                  <td className="px-6 py-3 text-[#94A3B8]">{m.requests.toLocaleString()}</td>
                </tr>
              ))}
              {Object.keys(memberTotals).length === 0 && (
                <tr>
                  <td colSpan={4} className="px-6 py-10 text-center text-sm text-[#64748B]">
                    No developer activity yet. Assign a service key to this project first.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
