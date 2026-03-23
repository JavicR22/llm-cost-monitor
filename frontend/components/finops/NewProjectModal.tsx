"use client";

import { useState } from "react";
import { createProject } from "@/lib/hooks/useFinOps";

interface Props {
  onClose: () => void;
  onCreated: () => void;
}

export function NewProjectModal({ onClose, onCreated }: Props) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [budget, setBudget] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim()) return;
    setLoading(true);
    setError(null);
    try {
      await createProject({
        name: name.trim(),
        description: description.trim() || undefined,
        budget_limit: budget ? parseFloat(budget) : undefined,
      });
      onCreated();
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create project");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div
        className="w-full max-w-md rounded-xl bg-[#1E293B] p-6 shadow-2xl"
        style={{ border: "1px solid #334155" }}
      >
        <h2 className="mb-5 text-lg font-semibold text-[#F8FAFC]">New Project</h2>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="mb-1.5 block text-xs font-medium text-[#94A3B8]">
              Project Name *
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. AI Chatbot"
              maxLength={255}
              required
              className="w-full rounded-lg bg-[#0F172A] px-3 py-2 text-sm text-[#F8FAFC] placeholder-[#64748B] outline-none focus:ring-1 focus:ring-[#3B82F6]"
              style={{ border: "1px solid #334155" }}
            />
          </div>

          <div>
            <label className="mb-1.5 block text-xs font-medium text-[#94A3B8]">
              Description
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Optional description"
              rows={2}
              maxLength={1000}
              className="w-full resize-none rounded-lg bg-[#0F172A] px-3 py-2 text-sm text-[#F8FAFC] placeholder-[#64748B] outline-none focus:ring-1 focus:ring-[#3B82F6]"
              style={{ border: "1px solid #334155" }}
            />
          </div>

          <div>
            <label className="mb-1.5 block text-xs font-medium text-[#94A3B8]">
              Monthly Budget Limit (USD)
            </label>
            <input
              type="number"
              value={budget}
              onChange={(e) => setBudget(e.target.value)}
              placeholder="e.g. 500"
              min="0.01"
              step="0.01"
              className="w-full rounded-lg bg-[#0F172A] px-3 py-2 text-sm text-[#F8FAFC] placeholder-[#64748B] outline-none focus:ring-1 focus:ring-[#3B82F6]"
              style={{ border: "1px solid #334155" }}
            />
          </div>

          {error && (
            <p className="rounded-lg bg-[#EF4444]/10 px-3 py-2 text-xs text-[#EF4444]">
              {error}
            </p>
          )}

          <div className="flex justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="rounded-lg px-4 py-2 text-sm font-medium text-[#94A3B8] transition-colors hover:text-[#F8FAFC]"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading || !name.trim()}
              className="rounded-lg bg-[#3B82F6] px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-[#2563EB] disabled:opacity-50"
            >
              {loading ? "Creating…" : "Create Project"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
