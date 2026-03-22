"use client";

import { useEffect, useState } from "react";
import { Copy, Check, AlertTriangle, X } from "lucide-react";

interface Props {
  rawKey: string;
  onClose: () => void;
}

export function RawKeyModal({ rawKey, onClose }: Props) {
  const [copied, setCopied] = useState(false);
  const [confirmed, setConfirmed] = useState(false);
  // Disable the close button for 3 seconds to force the user to see the key
  const [closeUnlocked, setCloseUnlocked] = useState(false);

  useEffect(() => {
    const t = setTimeout(() => setCloseUnlocked(true), 3000);
    return () => clearTimeout(t);
  }, []);

  async function handleCopy() {
    await navigator.clipboard.writeText(rawKey);
    setCopied(true);
    setTimeout(() => setCopied(false), 3000);
  }

  const canClose = closeUnlocked && confirmed;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4 backdrop-blur-sm">
      <div
        className="w-full max-w-lg rounded-xl shadow-2xl"
        style={{ background: "#1E293B", border: "1px solid #334155" }}
      >
        {/* Header */}
        <div className="flex items-center justify-between border-b border-[#334155] px-6 py-4">
          <h2 className="text-base font-semibold text-[#F8FAFC]">Your new API key</h2>
          <button
            onClick={onClose}
            disabled={!canClose}
            className="text-[#64748B] transition-colors hover:text-[#F8FAFC] disabled:cursor-not-allowed disabled:opacity-30"
          >
            <X size={18} />
          </button>
        </div>

        <div className="space-y-5 p-6">
          {/* High-impact warning banner */}
          <div
            className="flex items-start gap-3 rounded-lg px-4 py-3"
            style={{
              background: "rgba(245,158,11,0.12)",
              border: "2px solid rgba(245,158,11,0.5)",
            }}
          >
            <AlertTriangle size={18} className="mt-0.5 shrink-0 text-[#F59E0B]" />
            <div>
              <p className="text-sm font-bold text-[#F59E0B]">
                Copy your API key now — it won&apos;t be shown again
              </p>
              <p className="mt-0.5 text-xs text-[#D97706]">
                This key is stored as a one-way hash. There is no recovery option.
              </p>
            </div>
          </div>

          {/* Key field — contrasting background */}
          <div
            className="rounded-lg p-1"
            style={{ background: "#0F172A", border: "2px solid #3B82F6" }}
          >
            <div className="flex items-center gap-2 px-3 py-2">
              <code className="flex-1 break-all font-mono text-sm leading-relaxed text-[#93C5FD]">
                {rawKey}
              </code>
              <button
                onClick={handleCopy}
                className="shrink-0 flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-semibold transition-all"
                style={{
                  background: copied ? "rgba(16,185,129,0.15)" : "rgba(59,130,246,0.15)",
                  border: `1px solid ${copied ? "#10B981" : "#3B82F6"}`,
                  color: copied ? "#10B981" : "#60A5FA",
                }}
              >
                {copied ? (
                  <>
                    <Check size={13} />
                    Copied!
                  </>
                ) : (
                  <>
                    <Copy size={13} />
                    Copy
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Mandatory checkbox */}
          <label className="flex cursor-pointer items-start gap-3">
            <div className="mt-0.5 shrink-0">
              <input
                type="checkbox"
                checked={confirmed}
                onChange={(e) => setConfirmed(e.target.checked)}
                className="h-4 w-4 cursor-pointer rounded accent-[#3B82F6]"
              />
            </div>
            <span className="text-sm text-[#94A3B8]">
              I have copied my API key and stored it securely
            </span>
          </label>

          {/* Close button */}
          <button
            onClick={onClose}
            disabled={!canClose}
            className="w-full rounded-lg py-2.5 text-sm font-semibold text-white transition-all disabled:cursor-not-allowed disabled:opacity-40"
            style={{ background: canClose ? "#3B82F6" : "#334155" }}
          >
            {!closeUnlocked
              ? "Please read the key above…"
              : !confirmed
                ? "Check the box above to continue"
                : "Done — Close"}
          </button>
        </div>
      </div>
    </div>
  );
}
