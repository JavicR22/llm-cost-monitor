"use client";

import { useState } from "react";
import { inviteMember } from "@/lib/hooks/useFinOps";

interface Props {
  onCreated: () => void;
  onCancel: () => void;
}

export function InviteForm({ onCreated, onCancel }: Props) {
  const [form, setForm] = useState({ name: "", email: "", password: "", role: "viewer" });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function handleChange(e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await inviteMember(form);
      setForm({ name: "", email: "", password: "", role: "viewer" });
      onCreated();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to invite member.");
    } finally {
      setLoading(false);
    }
  }

  const inputCls =
    "w-full rounded-lg bg-[#0F172A] border border-[#334155] px-3 py-2 text-sm text-[#F8FAFC] placeholder-[#64748B] focus:border-[#3B82F6] focus:outline-none";

  return (
    <form
      onSubmit={handleSubmit}
      className="rounded-xl border border-[#334155] bg-[#1E293B] px-6 py-5 space-y-4"
    >
      <h3 className="text-sm font-semibold text-[#F8FAFC]">Invite a new member</h3>

      {error && (
        <p className="rounded-lg bg-[#EF4444]/10 border border-[#EF4444]/30 px-3 py-2 text-xs text-[#EF4444]">
          {error}
        </p>
      )}

      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="mb-1 block text-xs font-medium text-[#94A3B8]">Full name</label>
          <input
            name="name"
            value={form.name}
            onChange={handleChange}
            required
            placeholder="Jane Doe"
            className={inputCls}
          />
        </div>
        <div>
          <label className="mb-1 block text-xs font-medium text-[#94A3B8]">Email</label>
          <input
            name="email"
            type="email"
            value={form.email}
            onChange={handleChange}
            required
            placeholder="jane@company.com"
            className={inputCls}
          />
        </div>
        <div>
          <label className="mb-1 block text-xs font-medium text-[#94A3B8]">Password</label>
          <input
            name="password"
            type="password"
            value={form.password}
            onChange={handleChange}
            required
            minLength={8}
            placeholder="Min. 8 characters"
            className={inputCls}
          />
        </div>
        <div>
          <label className="mb-1 block text-xs font-medium text-[#94A3B8]">Role</label>
          <select name="role" value={form.role} onChange={handleChange} className={inputCls}>
            <option value="viewer">Viewer</option>
            <option value="admin">Admin</option>
          </select>
        </div>
      </div>

      <div className="flex justify-end gap-2">
        <button
          type="button"
          onClick={onCancel}
          className="rounded-lg px-4 py-2 text-sm font-medium text-[#94A3B8] hover:text-[#F8FAFC] transition-colors"
        >
          Cancel
        </button>
        <button
          type="submit"
          disabled={loading}
          className="rounded-lg bg-[#3B82F6] px-4 py-2 text-sm font-medium text-white hover:bg-[#2563EB] disabled:opacity-50 transition-colors"
        >
          {loading ? "Inviting…" : "Send Invite"}
        </button>
      </div>
    </form>
  );
}
