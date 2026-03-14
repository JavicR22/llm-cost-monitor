"use client";

import { useState } from "react";
import { Copy, Check, X } from "lucide-react";

interface Props {
  rawKey: string;
  onClose: () => void;
}

export function RawKeyModal({ rawKey, onClose }: Props) {
  const [copied, setCopied] = useState(false);

  async function handleCopy() {
    await navigator.clipboard.writeText(rawKey);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
      <div
        className="w-full max-w-lg rounded-xl shadow-2xl"
        style={{ background: "#1E293B", border: "1px solid #334155" }}
      >
        {/* Header */}
        <div className="flex items-center justify-between border-b border-[#334155] px-6 py-4">
          <h2 className="text-base font-semibold text-[#F8FAFC]">Save your API key</h2>
          <button onClick={onClose} className="text-[#64748B] hover:text-[#F8FAFC] transition-colors">
            <X size={18} />
          </button>
        </div>

        <div className="space-y-4 p-6">
          {/* Warning */}
          <div
            className="rounded-lg px-4 py-3"
            style={{ background: "rgba(245,158,11,0.1)", border: "1px solid rgba(245,158,11,0.3)" }}
          >
            <p className="text-xs font-medium text-[#F59E0B]">
              This key will only be shown once. Copy it now and store it securely.
            </p>
          </div>

          {/* Key display */}
          <div
            className="flex items-center gap-3 rounded-lg px-4 py-3"
            style={{ background: "#0F172A", border: "1px solid #334155" }}
          >
            <code className="flex-1 truncate font-mono text-sm text-[#F8FAFC]">
              {rawKey}
            </code>
            <button
              onClick={handleCopy}
              className="shrink-0 rounded-md p-1.5 transition-colors hover:bg-[#334155]"
              title="Copy to clipboard"
            >
              {copied ? (
                <Check size={15} className="text-[#10B981]" />
              ) : (
                <Copy size={15} className="text-[#94A3B8]" />
              )}
            </button>
          </div>

          <button
            onClick={onClose}
            className="w-full rounded-lg py-2 text-sm font-medium text-white transition-colors"
            style={{ background: "#3B82F6" }}
          >
            I've saved my key
          </button>
        </div>
      </div>
    </div>
  );
}
