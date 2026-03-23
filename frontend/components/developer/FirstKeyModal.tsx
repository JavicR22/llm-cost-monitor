"use client";

import { useState } from "react";
import { AlertTriangle, Copy, Check } from "lucide-react";

interface FirstKeyModalProps {
  rawKey: string;
  userId: string;
  onClose: () => void;
}

export function FirstKeyModal({ rawKey, userId, onClose }: FirstKeyModalProps) {
  const [copied, setCopied] = useState(false);
  const [confirmed, setConfirmed] = useState(false);

  async function handleCopy() {
    await navigator.clipboard.writeText(rawKey);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  function handleClose() {
    localStorage.setItem(`lcm_key_acknowledged_${userId}`, "1");
    onClose();
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm">
      <div
        className="w-full max-w-lg rounded-2xl shadow-2xl"
        style={{ background: "#1E293B", border: "1px solid #334155" }}
      >
        {/* Amber warning icon */}
        <div className="flex flex-col items-center px-8 pt-8 pb-4">
          <div
            className="mb-4 flex h-14 w-14 items-center justify-center rounded-full"
            style={{ background: "rgba(245,158,11,0.15)" }}
          >
            <AlertTriangle size={28} className="text-[#F59E0B]" />
          </div>

          <h2 className="text-center text-xl font-bold text-[#F8FAFC]">
            Tu API Key — Guárdala ahora
          </h2>
          <p className="mt-2 text-center text-sm text-[#94A3B8]">
            Esta es la única vez que verás tu Service API Key completa. Cópiala
            y guárdala en un lugar seguro. No podremos mostrártela de nuevo.
          </p>
        </div>

        <div className="space-y-5 px-8 pb-8">
          {/* Key display */}
          <div
            className="flex items-center gap-2 rounded-xl px-4 py-3"
            style={{ background: "#0F172A", border: "1px solid #334155" }}
          >
            <code className="min-w-0 flex-1 break-all font-mono text-sm leading-relaxed text-[#93C5FD]">
              {rawKey}
            </code>
            <button
              onClick={handleCopy}
              className="shrink-0 flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-semibold transition-all"
              style={{
                background: copied
                  ? "rgba(16,185,129,0.15)"
                  : "rgba(59,130,246,0.15)",
                border: `1px solid ${copied ? "#10B981" : "#3B82F6"}`,
                color: copied ? "#10B981" : "#60A5FA",
              }}
            >
              {copied ? (
                <>
                  <Check size={13} />
                  Copiado
                </>
              ) : (
                <>
                  <Copy size={13} />
                  Copiar
                </>
              )}
            </button>
          </div>

          {/* Checkbox */}
          <label className="flex cursor-pointer items-start gap-3">
            <input
              type="checkbox"
              checked={confirmed}
              onChange={(e) => setConfirmed(e.target.checked)}
              className="mt-0.5 h-4 w-4 cursor-pointer rounded accent-[#3B82F6]"
            />
            <span className="text-sm text-[#94A3B8]">
              Entiendo que esta key no se volverá a mostrar
            </span>
          </label>

          {/* Continue button */}
          <button
            onClick={handleClose}
            disabled={!confirmed}
            className="w-full rounded-xl py-3 text-sm font-semibold text-white transition-all disabled:cursor-not-allowed disabled:opacity-40"
            style={{ background: confirmed ? "#3B82F6" : "#334155" }}
          >
            Continuar
          </button>
        </div>
      </div>
    </div>
  );
}
