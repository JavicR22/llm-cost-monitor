"use client";

import { useState } from "react";
import { Plus, Trash2, Clock, Copy, Check } from "lucide-react";
import {
  useServiceKeys,
  createServiceKey,
  revokeServiceKey,
  type ServiceKey,
  type ServiceKeyCreated,
} from "@/lib/hooks/useKeys";
import { RawKeyModal } from "./RawKeyModal";

function fmtDate(iso: string | null) {
  if (!iso) return "Never";
  return new Intl.DateTimeFormat("en-US", {
    month: "short", day: "numeric", year: "numeric",
  }).format(new Date(iso));
}

function KeyRow({
  k,
  onRevoke,
}: {
  k: ServiceKey;
  onRevoke: (id: string) => Promise<void>;
}) {
  const [busy, setBusy] = useState(false);
  const [copied, setCopied] = useState(false);

  async function handleRevoke() {
    if (!confirm(`Revoke key "${k.key_prefix}"? This cannot be undone.`)) return;
    setBusy(true);
    try { await onRevoke(k.id); } finally { setBusy(false); }
  }

  async function handleCopy() {
    await navigator.clipboard.writeText(k.key_prefix);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  return (
    <div
      className="flex items-center gap-4 rounded-lg px-4 py-3"
      style={{ background: "#0F172A", border: "1px solid #334155" }}
    >
      {/* Active dot */}
      <span
        className="h-2 w-2 shrink-0 rounded-full"
        style={{ background: k.is_active ? "#10B981" : "#64748B" }}
      />

      {/* Key info */}
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <code className="font-mono text-sm text-[#F8FAFC]">{k.key_prefix}</code>
          {k.label && (
            <span className="rounded px-1.5 py-0.5 text-[10px] text-[#94A3B8]"
              style={{ background: "#334155" }}>
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

      {/* Copy prefix */}
      <button
        onClick={handleCopy}
        className="shrink-0 rounded p-1.5 text-[#64748B] transition-colors hover:bg-[#334155] hover:text-[#F8FAFC]"
        title="Copy key prefix"
      >
        {copied ? <Check size={14} className="text-green-400" /> : <Copy size={14} />}
      </button>

      {/* Revoke */}
      <button
        onClick={handleRevoke}
        disabled={busy || !k.is_active}
        className="shrink-0 rounded p-1.5 text-[#64748B] transition-colors hover:bg-red-500/10 hover:text-red-400 disabled:cursor-not-allowed disabled:opacity-30"
        title="Revoke key"
      >
        <Trash2 size={14} />
      </button>
    </div>
  );
}

export function ServiceKeysList() {
  const { data: keys, isLoading, mutate } = useServiceKeys();
  const [label, setLabel] = useState("");
  const [creating, setCreating] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [newKey, setNewKey] = useState<ServiceKeyCreated | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setCreating(true);
    setError(null);
    try {
      const created = await createServiceKey(label || undefined);
      setNewKey(created);
      setLabel("");
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
            Use these in your app's <code className="font-mono">base_url</code> requests
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
          className="flex items-center gap-3 border-b border-[#334155] px-5 py-3"
          style={{ background: "#0F172A" }}
        >
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
            className="rounded-lg px-4 py-1.5 text-xs font-medium text-white transition-colors"
            style={{ background: creating ? "#334155" : "#3B82F6", cursor: creating ? "not-allowed" : "pointer" }}
          >
            {creating ? "Creating…" : "Create"}
          </button>
          <button
            type="button"
            onClick={() => { setShowForm(false); setLabel(""); setError(null); }}
            className="text-xs text-[#64748B] hover:text-[#F8FAFC]"
          >
            Cancel
          </button>
        </form>
      )}

      {error && (
        <p className="mx-5 mt-3 rounded-lg bg-red-500/10 px-3 py-2 text-xs text-red-400">{error}</p>
      )}

      {/* List */}
      <div className="flex flex-col gap-2 p-4">
        {isLoading ? (
          Array.from({ length: 2 }).map((_, i) => (
            <div key={i} className="h-14 animate-pulse rounded-lg" style={{ background: "#0F172A" }} />
          ))
        ) : keys?.length === 0 ? (
          <p className="py-8 text-center text-sm text-[#64748B]">No service keys yet.</p>
        ) : (
          keys?.map((k) => (
            <KeyRow key={k.id} k={k} onRevoke={handleRevoke} />
          ))
        )}
      </div>

      {/* Raw key modal — shown once after creation */}
      {newKey && (
        <RawKeyModal rawKey={newKey.raw_key} onClose={() => setNewKey(null)} />
      )}
    </div>
  );
}
