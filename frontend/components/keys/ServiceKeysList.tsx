"use client";

import { useState } from "react";
import { Plus, Trash2, Clock, Check, ChevronDown, ChevronUp, FolderOpen, Users, User } from "lucide-react";
import {
  useServiceKeys,
  createServiceKey,
  revokeServiceKey,
  assignServiceKey,
  type ServiceKey,
  type ServiceKeyCreated,
} from "@/lib/hooks/useKeys";
import { useProjects, useTeams, useMembers } from "@/lib/hooks/useFinOps";
import { RawKeyModal } from "./RawKeyModal";

function fmtDate(iso: string | null) {
  if (!iso) return "Never";
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  }).format(new Date(iso));
}

// ------------------------------------------------------------------
// LayerAssign — hierarchical Project → Team → Developer selector
// ------------------------------------------------------------------

function LayerAssign({
  keyId,
  currentProjectId,
  currentTeamId,
  currentOwnerId,
  onAssigned,
}: {
  keyId: string;
  currentProjectId: string | null;
  currentTeamId: string | null;
  currentOwnerId: string | null;
  onAssigned: () => void;
}) {
  const { data: projects, mutate: mutateProjects } = useProjects();
  const { data: members } = useMembers();

  const [projectId, setProjectId] = useState(currentProjectId ?? "");
  const [teamId, setTeamId] = useState(currentTeamId ?? "");
  const [ownerId, setOwnerId] = useState(currentOwnerId ?? "");
  const [expanded, setExpanded] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  // Teams only load when a project is selected
  const { data: teams } = useTeams(projectId);

  // Reset team when project changes
  function handleProjectChange(val: string) {
    setProjectId(val);
    setTeamId("");
  }

  async function handleSave() {
    setSaving(true);
    try {
      await assignServiceKey(
        keyId,
        projectId || null,
        teamId || null,
        ownerId || null,
      );
      setSaved(true);
      setTimeout(() => setSaved(false), 2500);
      onAssigned();
      setExpanded(false);
      mutateProjects();
    } finally {
      setSaving(false);
    }
  }

  // Build summary label for collapsed state
  const projectName = projects?.find((p) => p.id === projectId)?.name;
  const teamName = teams?.find((t) => t.id === teamId)?.name;
  const ownerName = members?.find((m) => m.id === ownerId)?.name;

  const summaryParts = [
    projectName ?? "No project",
    teamName,
    ownerName,
  ].filter(Boolean);

  return (
    <div className="mt-1 pl-5">
      {/* Collapsed toggle */}
      <button
        type="button"
        onClick={() => setExpanded((v) => !v)}
        className="flex items-center gap-1.5 text-xs text-[#64748B] transition-colors hover:text-[#94A3B8]"
      >
        {saved ? (
          <Check size={11} className="text-[#10B981]" />
        ) : (
          <FolderOpen size={11} />
        )}
        <span className={saved ? "text-[#10B981]" : ""}>
          {saved ? "Saved" : summaryParts.join(" › ")}
        </span>
        {expanded ? <ChevronUp size={11} /> : <ChevronDown size={11} />}
      </button>

      {/* Expanded panel */}
      {expanded && (
        <div
          className="mt-2 space-y-2 rounded-lg p-3"
          style={{ background: "#0F172A", border: "1px solid #334155" }}
        >
          {/* Hierarchy label */}
          <p className="mb-1 text-[10px] font-semibold uppercase tracking-wider text-[#64748B]">
            Cost Attribution
          </p>

          {/* Project */}
          <div className="flex items-center gap-2">
            <FolderOpen size={12} className="shrink-0 text-[#3B82F6]" />
            <label className="w-20 text-xs text-[#64748B]">Project</label>
            <select
              value={projectId}
              onChange={(e) => handleProjectChange(e.target.value)}
              className="flex-1 rounded-md bg-[#1E293B] px-2 py-1 text-xs text-[#F8FAFC] outline-none"
              style={{ border: "1px solid #334155" }}
            >
              <option value="">— None —</option>
              {(projects ?? []).map((p) => (
                <option key={p.id} value={p.id}>{p.name}</option>
              ))}
            </select>
          </div>

          {/* Team — only shown when project selected and it has teams */}
          {projectId && (
            <div className="flex items-center gap-2">
              <Users size={12} className="shrink-0 text-[#10B981]" />
              <label className="w-20 text-xs text-[#64748B]">Team</label>
              <select
                value={teamId}
                onChange={(e) => setTeamId(e.target.value)}
                disabled={!teams || teams.length === 0}
                className="flex-1 rounded-md bg-[#1E293B] px-2 py-1 text-xs text-[#F8FAFC] outline-none disabled:opacity-40"
                style={{ border: "1px solid #334155" }}
              >
                <option value="">— None —</option>
                {(teams ?? []).map((t) => (
                  <option key={t.id} value={t.id}>{t.name}</option>
                ))}
              </select>
              {teams?.length === 0 && (
                <span className="text-[10px] text-[#64748B]">No teams</span>
              )}
            </div>
          )}

          {/* Developer (owner) */}
          <div className="flex items-center gap-2">
            <User size={12} className="shrink-0 text-[#F59E0B]" />
            <label className="w-20 text-xs text-[#64748B]">Developer</label>
            <select
              value={ownerId}
              onChange={(e) => setOwnerId(e.target.value)}
              className="flex-1 rounded-md bg-[#1E293B] px-2 py-1 text-xs text-[#F8FAFC] outline-none"
              style={{ border: "1px solid #334155" }}
            >
              <option value="">— None —</option>
              {(members ?? []).map((m) => (
                <option key={m.id} value={m.id}>
                  {m.name} ({m.role})
                </option>
              ))}
            </select>
          </div>

          {/* Hierarchy preview */}
          {(projectId || ownerId) && (
            <div
              className="rounded-md px-3 py-2 text-[10px] text-[#64748B]"
              style={{ background: "#1E293B" }}
            >
              <span className="text-[#94A3B8]">Attribution: </span>
              {[
                projectName && (
                  <span key="p" className="text-[#60A5FA]">{projectName}</span>
                ),
                teamName && (
                  <span key="t"> › <span className="text-[#34D399]">{teamName}</span></span>
                ),
                ownerName && (
                  <span key="o"> › <span className="text-[#FCD34D]">{ownerName}</span></span>
                ),
              ].filter(Boolean).length > 0
                ? [
                    projectName && <span key="p" className="text-[#60A5FA]">{projectName}</span>,
                    teamName && <span key="t"> › <span className="text-[#34D399]">{teamName}</span></span>,
                    ownerName && <span key="o"> › <span className="text-[#FCD34D]">{ownerName}</span></span>,
                  ]
                : "Not assigned"}
            </div>
          )}

          {/* Save button */}
          <button
            type="button"
            onClick={handleSave}
            disabled={saving}
            className="w-full rounded-md py-1.5 text-xs font-medium text-white transition-colors disabled:opacity-50"
            style={{ background: saving ? "#334155" : "#3B82F6" }}
          >
            {saving ? "Saving…" : "Save Attribution"}
          </button>
        </div>
      )}
    </div>
  );
}

// ------------------------------------------------------------------
// Single key row
// ------------------------------------------------------------------

function KeyRow({
  k,
  onRevoke,
  onMutate,
}: {
  k: ServiceKey;
  onRevoke: (id: string) => Promise<void>;
  onMutate: () => void;
}) {
  const [busy, setBusy] = useState(false);

  async function handleRevoke() {
    if (!confirm(`Revoke key "${k.key_prefix}"? This cannot be undone.`)) return;
    setBusy(true);
    try { await onRevoke(k.id); } finally { setBusy(false); }
  }

  return (
    <div
      className="rounded-lg px-4 py-3"
      style={{ background: "#0F172A", border: "1px solid #334155" }}
    >
      {/* Top: status + key + revoke */}
      <div className="flex items-center gap-3">
        <span
          className="h-2 w-2 shrink-0 rounded-full"
          style={{ background: k.is_active ? "#10B981" : "#64748B" }}
        />
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <code className="font-mono text-sm text-[#F8FAFC]">{k.key_prefix}</code>
            {k.label && (
              <span
                className="rounded px-1.5 py-0.5 text-[10px] text-[#94A3B8]"
                style={{ background: "#334155" }}
              >
                {k.label}
              </span>
            )}
          </div>
          <p className="mt-0.5 flex items-center gap-1 text-[11px] text-[#64748B]">
            <Clock size={10} />
            Created {fmtDate(k.created_at)}
            {k.last_used_at && ` · Last used ${fmtDate(k.last_used_at)}`}
          </p>
        </div>
        <button
          onClick={handleRevoke}
          disabled={busy || !k.is_active}
          className="shrink-0 rounded p-1.5 text-[#64748B] transition-colors hover:bg-red-500/10 hover:text-red-400 disabled:cursor-not-allowed disabled:opacity-30"
          title="Revoke key"
        >
          <Trash2 size={14} />
        </button>
      </div>

      {/* Layer assignment — collapsible */}
      <LayerAssign
        keyId={k.id}
        currentProjectId={k.project_id}
        currentTeamId={k.team_id}
        currentOwnerId={k.owner_user_id}
        onAssigned={onMutate}
      />
    </div>
  );
}

// ------------------------------------------------------------------
// Main component
// ------------------------------------------------------------------

export function ServiceKeysList() {
  const { data: keys, isLoading, mutate } = useServiceKeys();
  const { data: projects } = useProjects();

  const [label, setLabel] = useState("");
  const [createProjectId, setCreateProjectId] = useState("");
  const [creating, setCreating] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [newKey, setNewKey] = useState<ServiceKeyCreated | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setCreating(true);
    setError(null);
    try {
      const created = await createServiceKey(label || undefined, createProjectId || null);
      setNewKey(created);
      setLabel("");
      setCreateProjectId("");
      setShowForm(false);
      await mutate();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create key");
    } finally {
      setCreating(false);
    }
  }

  async function handleRevoke(id: string) {
    await revokeServiceKey(id);
    await mutate((current) => current?.filter((k) => k.id !== id), { revalidate: false });
  }

  return (
    <div
      className="flex flex-col rounded-xl"
      style={{ background: "#1E293B", border: "1px solid #334155" }}
    >
      {/* Header */}
      <div className="flex items-center justify-between border-b border-[#334155] px-5 py-4">
        <div>
          <h2 className="text-sm font-semibold text-[#F8FAFC]">Service API Keys</h2>
          <p className="text-xs text-[#64748B]">
            Use these in your app&apos;s <code className="font-mono">base_url</code> requests
          </p>
        </div>
        <button
          onClick={() => { setShowForm(!showForm); setError(null); }}
          className="flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium text-white transition-colors hover:bg-[#2563EB]"
          style={{ background: "#3B82F6" }}
        >
          <Plus size={13} />
          New Key
        </button>
      </div>

      {/* Inline create form */}
      {showForm && (
        <form
          onSubmit={handleCreate}
          className="flex flex-col gap-3 border-b border-[#334155] px-5 py-4"
          style={{ background: "#0F172A" }}
        >
          <div className="flex items-center gap-3">
            <input
              type="text"
              value={label}
              onChange={(e) => setLabel(e.target.value)}
              placeholder="Label (optional)"
              maxLength={100}
              className="flex-1 rounded-lg px-3 py-1.5 text-sm text-[#F8FAFC] outline-none"
              style={{ background: "#1E293B", border: "1px solid #334155" }}
            />
            <button
              type="submit"
              disabled={creating}
              className="rounded-lg px-4 py-1.5 text-xs font-medium text-white transition-colors disabled:cursor-not-allowed"
              style={{ background: creating ? "#334155" : "#3B82F6" }}
            >
              {creating ? "Creating…" : "Create"}
            </button>
            <button
              type="button"
              onClick={() => { setShowForm(false); setLabel(""); setCreateProjectId(""); setError(null); }}
              className="text-xs text-[#64748B] hover:text-[#F8FAFC]"
            >
              Cancel
            </button>
          </div>

          {/* Optional project at creation */}
          {(projects ?? []).length > 0 && (
            <div className="flex items-center gap-2">
              <FolderOpen size={13} className="shrink-0 text-[#64748B]" />
              <label className="text-xs text-[#64748B]">Assign to project:</label>
              <select
                value={createProjectId}
                onChange={(e) => setCreateProjectId(e.target.value)}
                className="rounded-md bg-[#1E293B] px-2 py-1 text-xs text-[#94A3B8] outline-none"
                style={{ border: "1px solid #334155" }}
              >
                <option value="">None</option>
                {(projects ?? []).map((p) => (
                  <option key={p.id} value={p.id}>{p.name}</option>
                ))}
              </select>
            </div>
          )}
        </form>
      )}

      {error && (
        <p className="mx-5 mt-3 rounded-lg bg-red-500/10 px-3 py-2 text-xs text-red-400">{error}</p>
      )}

      {/* List */}
      <div className="flex flex-col gap-2 p-4">
        {isLoading
          ? Array.from({ length: 2 }).map((_, i) => (
              <div key={i} className="h-16 animate-pulse rounded-lg" style={{ background: "#0F172A" }} />
            ))
          : keys?.length === 0
            ? <p className="py-8 text-center text-sm text-[#64748B]">No service keys yet.</p>
            : keys?.map((k) => (
                <KeyRow key={k.id} k={k} onRevoke={handleRevoke} onMutate={() => mutate()} />
              ))}
      </div>

      {newKey && (
        <RawKeyModal rawKey={newKey.raw_key} onClose={() => setNewKey(null)} />
      )}
    </div>
  );
}
