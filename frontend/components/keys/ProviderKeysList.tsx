"use client";

import { useState } from "react";
import { Plus, Trash2, Eye, EyeOff, X } from "lucide-react";
import {
  useProviderKeys,
  createProviderKey,
  revokeProviderKey,
  type ProviderKey,
  type ProviderName,
} from "@/lib/hooks/useKeys";

const PROVIDERS: { value: ProviderName; label: string; color: string }[] = [
  { value: "openai",    label: "OpenAI",    color: "#3B82F6" },
  { value: "anthropic", label: "Anthropic", color: "#F97316" },
  { value: "google",    label: "Google",    color: "#10B981" },
  { value: "mistral",   label: "Mistral",   color: "#8B5CF6" },
];

function ProviderBadge({ provider }: { provider: string }) {
  const p = PROVIDERS.find((x) => x.value === provider);
  return (
    <span
      className="rounded px-2 py-0.5 text-[11px] font-semibold"
      style={{ background: `${p?.color ?? "#64748B"}20`, color: p?.color ?? "#64748B" }}
    >
      {p?.label ?? provider}
    </span>
  );
}

function KeyRow({
  k,
  onRevoke,
}: {
  k: ProviderKey;
  onRevoke: (id: string) => Promise<void>;
}) {
  const [busy, setBusy] = useState(false);

  async function handleRevoke() {
    if (!confirm(`Revoke this ${k.provider} key? The proxy will stop using it immediately.`)) return;
    setBusy(true);
    try { await onRevoke(k.id); } finally { setBusy(false); }
  }

  return (
    <div
      className="flex items-center gap-4 rounded-lg px-4 py-3"
      style={{ background: "#0F172A", border: "1px solid #334155" }}
    >
      <ProviderBadge provider={k.provider} />

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
        <p className="mt-0.5 text-[11px] text-[#64748B]">
          Added {new Intl.DateTimeFormat("en-US", { month: "short", day: "numeric", year: "numeric" })
            .format(new Date(k.created_at))}
        </p>
      </div>

      <span
        className="h-2 w-2 shrink-0 rounded-full"
        style={{ background: k.is_active ? "#10B981" : "#64748B" }}
      />

      <button
        onClick={handleRevoke}
        disabled={busy || !k.is_active}
        className="shrink-0 rounded p-1.5 text-[#64748B] transition-colors hover:bg-red-500/10 hover:text-red-400 disabled:cursor-not-allowed disabled:opacity-30"
        title="Revoke"
      >
        <Trash2 size={14} />
      </button>
    </div>
  );
}

function AddProviderKeyModal({
  onClose,
  onCreated,
}: {
  onClose: () => void;
  onCreated: () => void;
}) {
  const [provider, setProvider] = useState<ProviderName>("openai");
  const [rawKey, setRawKey] = useState("");
  const [label, setLabel] = useState("");
  const [showKey, setShowKey] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      await createProviderKey(provider, rawKey, label || undefined);
      onCreated();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to add key");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
      <div
        className="w-full max-w-md rounded-xl shadow-2xl"
        style={{ background: "#1E293B", border: "1px solid #334155" }}
      >
        <div className="flex items-center justify-between border-b border-[#334155] px-6 py-4">
          <h2 className="text-base font-semibold text-[#F8FAFC]">Add Provider Key</h2>
          <button onClick={onClose} className="text-[#64748B] hover:text-[#F8FAFC] transition-colors">
            <X size={18} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4 p-6">
          {/* Provider selector */}
          <div className="space-y-2">
            <label className="text-xs font-medium text-[#94A3B8]">Provider</label>
            <div className="grid grid-cols-2 gap-2">
              {PROVIDERS.map((p) => (
                <button
                  key={p.value}
                  type="button"
                  onClick={() => setProvider(p.value)}
                  className="rounded-lg py-2 text-sm font-medium transition-colors"
                  style={{
                    background: provider === p.value ? `${p.color}20` : "#0F172A",
                    border: `1px solid ${provider === p.value ? p.color : "#334155"}`,
                    color: provider === p.value ? p.color : "#94A3B8",
                  }}
                >
                  {p.label}
                </button>
              ))}
            </div>
          </div>

          {/* API Key input */}
          <div className="space-y-2">
            <label className="text-xs font-medium text-[#94A3B8]">API Key</label>
            <div className="relative">
              <input
                type={showKey ? "text" : "password"}
                required
                value={rawKey}
                onChange={(e) => setRawKey(e.target.value)}
                placeholder="sk-..."
                className="w-full rounded-lg py-2 pl-3 pr-10 text-sm font-mono text-[#F8FAFC] outline-none"
                style={{ background: "#0F172A", border: "1px solid #334155" }}
              />
              <button
                type="button"
                onClick={() => setShowKey(!showKey)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-[#64748B] hover:text-[#94A3B8]"
              >
                {showKey ? <EyeOff size={14} /> : <Eye size={14} />}
              </button>
            </div>
            <p className="text-[10px] text-[#64748B]">
              Stored encrypted at rest. Never returned via the API.
            </p>
          </div>

          {/* Label */}
          <div className="space-y-2">
            <label className="text-xs font-medium text-[#94A3B8]">Label (optional)</label>
            <input
              type="text"
              value={label}
              onChange={(e) => setLabel(e.target.value)}
              placeholder="e.g. Production"
              maxLength={100}
              className="w-full rounded-lg px-3 py-2 text-sm text-[#F8FAFC] outline-none"
              style={{ background: "#0F172A", border: "1px solid #334155" }}
            />
          </div>

          {error && (
            <p className="rounded-lg bg-red-500/10 px-3 py-2 text-xs text-red-400">{error}</p>
          )}

          <div className="flex gap-3 pt-1">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 rounded-lg py-2 text-sm font-medium text-[#94A3B8]"
              style={{ background: "#0F172A", border: "1px solid #334155" }}
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={saving}
              className="flex-1 rounded-lg py-2 text-sm font-medium text-white"
              style={{ background: saving ? "#334155" : "#3B82F6", cursor: saving ? "not-allowed" : "pointer" }}
            >
              {saving ? "Adding…" : "Add Key"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export function ProviderKeysList() {
  const { data: keys, isLoading, mutate } = useProviderKeys();
  const [showModal, setShowModal] = useState(false);

  async function handleRevoke(id: string) {
    await revokeProviderKey(id);
    await mutate((current) => current?.filter((k) => k.id !== id), { revalidate: false });
  }

  return (
    <div
      className="flex flex-col rounded-xl"
      style={{ background: "#1E293B", border: "1px solid #334155" }}
    >
      <div className="flex items-center justify-between border-b border-[#334155] px-5 py-4">
        <div>
          <h2 className="text-sm font-semibold text-[#F8FAFC]">Provider API Keys</h2>
          <p className="text-xs text-[#64748B]">
            Encrypted at rest — used by the proxy to forward requests
          </p>
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium text-white transition-colors hover:bg-[#2563EB]"
          style={{ background: "#3B82F6" }}
        >
          <Plus size={13} />
          Add Key
        </button>
      </div>

      <div className="flex flex-col gap-2 p-4">
        {isLoading ? (
          Array.from({ length: 2 }).map((_, i) => (
            <div key={i} className="h-14 animate-pulse rounded-lg" style={{ background: "#0F172A" }} />
          ))
        ) : keys?.length === 0 ? (
          <p className="py-8 text-center text-sm text-[#64748B]">No provider keys yet.</p>
        ) : (
          keys?.map((k) => (
            <KeyRow key={k.id} k={k} onRevoke={handleRevoke} />
          ))
        )}
      </div>

      {showModal && (
        <AddProviderKeyModal
          onClose={() => setShowModal(false)}
          onCreated={async () => {
            setShowModal(false);
            await mutate();
          }}
        />
      )}
    </div>
  );
}
