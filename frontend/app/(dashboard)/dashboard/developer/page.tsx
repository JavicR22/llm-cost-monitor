"use client";

import { useState } from "react";
import useSWR from "swr";
import { Key, Clock, RefreshCw, AlertCircle, FolderOpen, Users } from "lucide-react";
import { authedFetcher, authedClient } from "@/lib/api";
import { useDevelopersAnalytics } from "@/lib/hooks/useAnalytics";
import { useProjects } from "@/lib/hooks/useFinOps";
import { FirstKeyModal } from "@/components/developer/FirstKeyModal";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface MeResponse {
  id: string;
  name: string;
  email: string;
  role: string;
  assigned_project_id: string | null;
  assigned_team_id: string | null;
  has_seen_key_modal: boolean;
}

interface DeveloperKeyInfo {
  key_prefix: string;
  created_at: string;
  last_used_at: string | null;
  is_active: boolean;
}

interface GeneratedKey {
  raw_key: string;
  key_prefix: string;
  created_at: string;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function fmtDate(iso: string | null) {
  if (!iso) return "Never";
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  }).format(new Date(iso));
}

function fmtUsd(v: string | number) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 2,
    maximumFractionDigits: 4,
  }).format(Number(v));
}

function fmtNum(v: number | string) {
  return new Intl.NumberFormat("en-US").format(Number(v));
}

function fmtTokens(v: number | string) {
  const n = Number(v);
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}k`;
  return String(n);
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function StatCard({
  label,
  value,
  color,
}: {
  label: string;
  value: string;
  color: string;
}) {
  return (
    <div
      className="flex-1 rounded-xl px-6 py-5"
      style={{ background: "#1E293B", border: "1px solid #334155" }}
    >
      <p className="text-xs font-medium uppercase tracking-wider text-[#64748B]">
        {label}
      </p>
      <p className="mt-2 text-2xl font-semibold" style={{ color }}>
        {value}
      </p>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------

export default function DeveloperPage() {
  const [regenerating, setRegenerating] = useState(false);
  const [pendingKey, setPendingKey] = useState<GeneratedKey | null>(null);

  const { data: me } = useSWR<MeResponse>("/api/v1/auth/me", authedFetcher);
  const {
    data: devKey,
    isLoading: keyLoading,
    mutate: mutateKey,
  } = useSWR<DeveloperKeyInfo | null>(
    me ? "/api/v1/developer-keys/me" : null,
    authedFetcher,
    { shouldRetryOnError: false }
  );

  const projectId = me?.assigned_project_id ?? "";
  const { data: projects } = useProjects();
  const { data: devAnalytics } = useDevelopersAnalytics(projectId, "30d");

  const myProject = (projects ?? []).find((p) => p.id === projectId);
  const myMetrics = me
    ? (devAnalytics ?? []).find((d) => d.user_id === me.id)
    : null;

  // Check if we should auto-show the key modal
  // (Only triggers once: when has_seen_key_modal is false AND no localStorage flag)
  const [modalDismissed, setModalDismissed] = useState(false);

  const acknowledged =
    typeof window !== "undefined" && me
      ? !!localStorage.getItem(`lcm_key_acknowledged_${me.id}`)
      : false;

  const shouldShowModal =
    !modalDismissed &&
    !!pendingKey &&
    !!me &&
    !acknowledged;

  async function handleGenerateKey() {
    setRegenerating(true);
    try {
      // If key exists, revoke first
      if (devKey) {
        await authedClient<void>("/api/v1/developer-keys/me", {
          method: "DELETE",
        });
      }
      const generated = await authedClient<GeneratedKey>(
        "/api/v1/developer-keys/generate",
        { method: "POST" }
      );
      setPendingKey(generated);
      await mutateKey();
    } finally {
      setRegenerating(false);
    }
  }

  function handleModalClose() {
    setModalDismissed(true);
    setPendingKey(null);
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-semibold text-[#F8FAFC]">
          My Developer Dashboard
        </h1>
        <p className="mt-1 text-sm text-[#94A3B8]">
          Welcome back, {me?.name ?? "…"}
        </p>
      </div>

      {/* My API Key */}
      <div
        className="rounded-xl p-6"
        style={{ background: "#1E293B", border: "1px solid #334155" }}
      >
        <div className="mb-4 flex items-center gap-2">
          <Key size={16} className="text-[#3B82F6]" />
          <h2 className="text-base font-semibold text-[#F8FAFC]">My API Key</h2>
        </div>

        {keyLoading ? (
          <div className="h-12 animate-pulse rounded-lg bg-[#334155]" />
        ) : devKey ? (
          <div className="space-y-3">
            <div
              className="flex items-center gap-3 rounded-lg px-4 py-3"
              style={{ background: "#0F172A", border: "1px solid #334155" }}
            >
              <span
                className="h-2 w-2 shrink-0 rounded-full"
                style={{ background: devKey.is_active ? "#10B981" : "#64748B" }}
              />
              <code className="flex-1 font-mono text-sm text-[#F8FAFC]">
                {devKey.key_prefix}…
              </code>
            </div>
            <div className="flex items-center gap-4 text-xs text-[#64748B]">
              <span className="flex items-center gap-1">
                <Clock size={11} />
                Created {fmtDate(devKey.created_at)}
              </span>
              <span className="flex items-center gap-1">
                <Clock size={11} />
                Last used {fmtDate(devKey.last_used_at)}
              </span>
            </div>
            <button
              onClick={handleGenerateKey}
              disabled={regenerating}
              className="flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium text-white transition-colors disabled:opacity-50"
              style={{
                background: regenerating ? "#334155" : "rgba(239,68,68,0.15)",
                border: "1px solid rgba(239,68,68,0.4)",
                color: regenerating ? "#94A3B8" : "#F87171",
              }}
            >
              <RefreshCw size={14} className={regenerating ? "animate-spin" : ""} />
              {regenerating ? "Regenerating…" : "Revoke & Regenerate"}
            </button>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="flex items-center gap-3 text-sm text-[#94A3B8]">
              <AlertCircle size={16} className="text-[#F59E0B]" />
              You don&apos;t have an API key yet. Generate one to start using the proxy.
            </div>
            <button
              onClick={handleGenerateKey}
              disabled={regenerating}
              className="flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium text-white transition-colors disabled:opacity-50"
              style={{ background: regenerating ? "#334155" : "#3B82F6" }}
            >
              <Key size={14} />
              {regenerating ? "Generating…" : "Generate My API Key"}
            </button>
          </div>
        )}
      </div>

      {/* My Project */}
      <div
        className="rounded-xl p-6"
        style={{ background: "#1E293B", border: "1px solid #334155" }}
      >
        <div className="mb-4 flex items-center gap-2">
          <FolderOpen size={16} className="text-[#10B981]" />
          <h2 className="text-base font-semibold text-[#F8FAFC]">My Project</h2>
        </div>

        {!projectId ? (
          <p className="text-sm text-[#64748B]">
            You have not been assigned to a project yet. Contact your admin.
          </p>
        ) : myProject ? (
          <div className="space-y-2">
            <p className="font-medium text-[#F8FAFC]">{myProject.name}</p>
            {myProject.description && (
              <p className="text-sm text-[#94A3B8]">{myProject.description}</p>
            )}
            {me?.assigned_team_id && (
              <div className="flex items-center gap-1.5 text-xs text-[#64748B]">
                <Users size={12} />
                Assigned to a team within this project
              </div>
            )}
          </div>
        ) : (
          <div className="h-8 w-48 animate-pulse rounded bg-[#334155]" />
        )}
      </div>

      {/* My Metrics (30d) */}
      <div>
        <h2 className="mb-4 text-base font-semibold text-[#F8FAFC]">
          My Usage (Last 30 days)
        </h2>

        {!projectId ? (
          <p className="text-sm text-[#64748B]">
            Assign to a project to see your metrics.
          </p>
        ) : (
          <div className="flex gap-4">
            <StatCard
              label="Spend"
              value={myMetrics ? fmtUsd(myMetrics.spend_30d) : "—"}
              color="#3B82F6"
            />
            <StatCard
              label="Requests"
              value={myMetrics ? fmtNum(myMetrics.requests_30d) : "—"}
              color="#10B981"
            />
            <StatCard
              label="Tokens"
              value={myMetrics ? fmtTokens(myMetrics.tokens_30d) : "—"}
              color="#F59E0B"
            />
          </div>
        )}
      </div>

      {/* First-time key modal */}
      {shouldShowModal && pendingKey && me && (
        <FirstKeyModal
          rawKey={pendingKey.raw_key}
          userId={me.id}
          onClose={handleModalClose}
        />
      )}
    </div>
  );
}
