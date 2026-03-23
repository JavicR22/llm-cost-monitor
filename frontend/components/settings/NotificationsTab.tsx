"use client";

import { useState } from "react";
import { Mail, Plus, Trash2, Bell } from "lucide-react";
import {
  useNotificationChannels,
  addNotificationChannel,
  removeNotificationChannel,
  type NotificationChannel,
} from "@/lib/hooks/useNotificationChannels";

function ChannelRow({
  ch,
  onRemove,
}: {
  ch: NotificationChannel;
  onRemove: (id: string) => Promise<void>;
}) {
  const [busy, setBusy] = useState(false);

  async function handleRemove() {
    if (!confirm(`Remove notification channel "${ch.display_hint}"?`)) return;
    setBusy(true);
    try { await onRemove(ch.id); } finally { setBusy(false); }
  }

  return (
    <div
      className="flex items-center gap-4 rounded-lg px-4 py-3"
      style={{ background: "#0F172A", border: "1px solid #334155" }}
    >
      <div
        className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg"
        style={{ background: "rgba(59,130,246,0.15)" }}
      >
        <Mail size={15} color="#3B82F6" />
      </div>

      <div className="min-w-0 flex-1">
        <p className="text-sm text-[#F8FAFC]">{ch.display_hint}</p>
        <p className="text-[11px] text-[#64748B]">
          Email · Added {new Intl.DateTimeFormat("en-US", {
            month: "short", day: "numeric", year: "numeric",
          }).format(new Date(ch.created_at))}
        </p>
      </div>

      <span
        className="h-2 w-2 shrink-0 rounded-full"
        style={{ background: ch.is_active ? "#10B981" : "#64748B" }}
      />

      <button
        onClick={handleRemove}
        disabled={busy}
        className="shrink-0 rounded p-1.5 text-[#64748B] transition-colors hover:bg-red-500/10 hover:text-red-400 disabled:opacity-30"
        title="Remove"
      >
        <Trash2 size={14} />
      </button>
    </div>
  );
}

export function NotificationsTab() {
  const { data: channels, isLoading, mutate } = useNotificationChannels();
  const [showForm, setShowForm] = useState(false);
  const [email, setEmail] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleAdd(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      await addNotificationChannel(email);
      setEmail("");
      setShowForm(false);
      await mutate();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to add channel");
    } finally {
      setSaving(false);
    }
  }

  async function handleRemove(id: string) {
    await removeNotificationChannel(id);
    await mutate();
  }

  return (
    <div className="space-y-6">
      {/* Info banner */}
      <div
        className="flex items-start gap-3 rounded-xl px-4 py-3"
        style={{ background: "rgba(59,130,246,0.08)", border: "1px solid rgba(59,130,246,0.2)" }}
      >
        <Bell size={16} color="#3B82F6" className="mt-0.5 shrink-0" />
        <p className="text-xs text-[#94A3B8]">
          Email notifications are sent when circuit breakers trip, hard budget limits are hit,
          or anomalous spending is detected. Soft-limit warnings are also delivered to all
          configured channels.
        </p>
      </div>

      {/* Channel list */}
      <div
        className="rounded-xl"
        style={{ background: "#1E293B", border: "1px solid #334155" }}
      >
        <div className="flex items-center justify-between border-b border-[#334155] px-5 py-4">
          <div>
            <h3 className="text-sm font-semibold text-[#F8FAFC]">Email Channels</h3>
            <p className="text-xs text-[#64748B]">{channels?.length ?? 0} configured</p>
          </div>
          <button
            onClick={() => { setShowForm(!showForm); setError(null); }}
            className="flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium text-white transition-colors hover:bg-[#2563EB]"
            style={{ background: "#3B82F6" }}
          >
            <Plus size={13} />
            Add Email
          </button>
        </div>

        {/* Inline add form */}
        {showForm && (
          <form
            onSubmit={handleAdd}
            className="flex items-center gap-3 border-b border-[#334155] px-5 py-3"
            style={{ background: "#0F172A" }}
          >
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="alerts@yourcompany.com"
              className="flex-1 rounded-lg px-3 py-1.5 text-sm text-[#F8FAFC] outline-none"
              style={{ background: "#1E293B", border: "1px solid #334155" }}
            />
            <button
              type="submit"
              disabled={saving}
              className="rounded-lg px-4 py-1.5 text-xs font-medium text-white"
              style={{ background: saving ? "#334155" : "#3B82F6", cursor: saving ? "not-allowed" : "pointer" }}
            >
              {saving ? "Adding…" : "Add"}
            </button>
            <button
              type="button"
              onClick={() => { setShowForm(false); setEmail(""); setError(null); }}
              className="text-xs text-[#64748B] hover:text-[#F8FAFC]"
            >
              Cancel
            </button>
          </form>
        )}

        {error && (
          <p className="mx-5 mt-3 rounded-lg bg-red-500/10 px-3 py-2 text-xs text-red-400">{error}</p>
        )}

        <div className="flex flex-col gap-2 p-4">
          {isLoading ? (
            Array.from({ length: 2 }).map((_, i) => (
              <div key={i} className="h-14 animate-pulse rounded-lg" style={{ background: "#0F172A" }} />
            ))
          ) : channels?.length === 0 ? (
            <p className="py-8 text-center text-sm text-[#64748B]">
              No notification channels configured.
            </p>
          ) : (
            channels?.map((ch) => (
              <ChannelRow key={ch.id} ch={ch} onRemove={handleRemove} />
            ))
          )}
        </div>
      </div>
    </div>
  );
}
