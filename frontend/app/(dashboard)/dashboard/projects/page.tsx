"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { FolderOpen, Plus, Trash2 } from "lucide-react";

import { useProjects, useSummaryReport, deleteProject } from "@/lib/hooks/useFinOps";
import { NewProjectModal } from "@/components/finops/NewProjectModal";
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

export default function ProjectsPage() {
  const router = useRouter();
  const { data: projects, isLoading, mutate } = useProjects();
  const { data: summary } = useSummaryReport(FROM_30, TODAY);
  const [showModal, setShowModal] = useState(false);
  const [deleting, setDeleting] = useState<string | null>(null);

  const spendByProject = Object.fromEntries(
    (summary ?? []).map((s) => [s.project_id, s])
  );

  async function handleDelete(id: string, e: React.MouseEvent) {
    e.preventDefault();
    e.stopPropagation();
    if (!confirm("Delete this project and all its teams?")) return;
    setDeleting(id);
    try {
      await deleteProject(id);
      mutate();
    } finally {
      setDeleting(null);
    }
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-[#F8FAFC]">Projects</h1>
          <p className="mt-1 text-sm text-[#94A3B8]">
            Track LLM costs by project, team, and developer.
          </p>
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="flex items-center gap-2 rounded-lg bg-[#3B82F6] px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-[#2563EB]"
        >
          <Plus size={16} />
          New Project
        </button>
      </div>

      {/* Table */}
      <div className="overflow-hidden rounded-xl bg-[#1E293B]" style={{ border: "1px solid #334155" }}>
        <div className="border-b border-[#0F172A] bg-[#0F172A] px-6 py-4">
          <h3 className="text-base font-semibold text-[#F8FAFC]">All Projects</h3>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-[#0F172A] bg-[#0F172A]">
                {["Project", "Spend (30d)", "Requests", "Budget", ""].map((col) => (
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
              {isLoading
                ? Array.from({ length: 4 }).map((_, i) => (
                    <tr key={i} className={i % 2 === 1 ? "bg-[#0F172A]" : ""}>
                      {Array.from({ length: 5 }).map((_, j) => (
                        <td key={j} className="px-6 py-4">
                          <div className="h-4 animate-pulse rounded bg-[#334155]" />
                        </td>
                      ))}
                    </tr>
                  ))
                : (projects ?? []).map((project, i) => {
                    const spend = spendByProject[project.id];
                    const totalCost = spend ? Number(spend.total_cost) : 0;
                    const budgetLimit = project.budget_limit
                      ? Number(project.budget_limit)
                      : null;

                    return (
                      <tr
                        key={project.id}
                        className={`cursor-pointer transition-colors hover:bg-[#334155]/30 ${i % 2 === 1 ? "bg-[#0F172A]" : ""}`}
                        onClick={() => router.push(`/dashboard/projects/${project.id}`)}
                      >
                        {/* Name */}
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-3">
                            <FolderOpen size={16} className="shrink-0 text-[#3B82F6]" />
                            <div>
                              <p className="font-medium text-[#F8FAFC]">{project.name}</p>
                              {project.description && (
                                <p className="mt-0.5 text-xs text-[#64748B]">
                                  {project.description}
                                </p>
                              )}
                            </div>
                          </div>
                        </td>

                        {/* Spend */}
                        <td className="px-6 py-4 font-mono text-[#F8FAFC]">
                          {fmtUsd(totalCost)}
                        </td>

                        {/* Requests */}
                        <td className="px-6 py-4 text-[#94A3B8]">
                          {spend ? spend.requests.toLocaleString() : "—"}
                        </td>

                        {/* Budget */}
                        <td className="px-6 py-4 min-w-[180px]">
                          {budgetLimit ? (
                            <BudgetBar spent={totalCost} limit={budgetLimit} />
                          ) : (
                            <span className="text-xs text-[#64748B]">No limit</span>
                          )}
                        </td>

                        {/* Actions */}
                        <td className="px-6 py-4 text-right">
                          <button
                            onClick={(e) => handleDelete(project.id, e)}
                            disabled={deleting === project.id}
                            className="rounded p-1 text-[#64748B] transition-colors hover:text-[#EF4444] disabled:opacity-40"
                          >
                            <Trash2 size={14} />
                          </button>
                        </td>
                      </tr>
                    );
                  })}

              {!isLoading && (projects ?? []).length === 0 && (
                <tr>
                  <td colSpan={5} className="px-6 py-12 text-center text-sm text-[#64748B]">
                    No projects yet. Create one to start tracking costs.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {showModal && (
        <NewProjectModal
          onClose={() => setShowModal(false)}
          onCreated={() => mutate()}
        />
      )}
    </div>
  );
}
