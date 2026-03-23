"use client";

import type { Range } from "@/lib/hooks/useAnalytics";

interface RangeSelectorProps {
  value: Range;
  onChange: (r: Range) => void;
}

const RANGES: { key: Range; label: string }[] = [
  { key: "7d", label: "7d" },
  { key: "30d", label: "30d" },
  { key: "90d", label: "90d" },
];

export function RangeSelector({ value, onChange }: RangeSelectorProps) {
  return (
    <div className="flex items-center rounded-lg p-1" style={{ background: "#0F172A" }}>
      {RANGES.map(({ key, label }) => (
        <button
          key={key}
          onClick={() => onChange(key)}
          className="rounded-md px-3 py-1.5 text-xs font-medium transition-colors"
          style={{
            background: value === key ? "#334155" : "transparent",
            color: value === key ? "#F8FAFC" : "#94A3B8",
          }}
        >
          {label}
        </button>
      ))}
    </div>
  );
}
