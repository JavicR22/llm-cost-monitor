"use client";

import { useState } from "react";
import { Users, ChevronUp, ChevronDown } from "lucide-react";
import type { DeveloperAnalytics } from "@/lib/hooks/useAnalytics";

interface DevelopersTabProps {
  developers: DeveloperAnalytics[];
  loading: boolean;
}

type SortKey = "name" | "spend_30d" | "requests_30d" | "tokens_30d" | "last_active";

function fmtUsd(v: string | number) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 2,
    maximumFractionDigits: 4,
  }).format(Number(v));
}

function fmtNum(v: number | string) {
  return new Intl.NumberFormat("en-US").format(Number(v));
}

function fmtTokens(v: number | string) {
  const n = Number(v);
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}k`;
  return String(n);
}

function fmtDate(iso: string | null) {
  if (!iso) return "Never";
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
  }).format(new Date(iso));
}

const COLUMNS: { key: SortKey; label: string }[] = [
  { key: "name", label: "Name" },
  { key: "spend_30d", label: "Spend (30d)" },
  { key: "requests_30d", label: "Requests" },
  { key: "tokens_30d", label: "Tokens" },
  { key: "last_active", label: "Last Active" },
];

export function DevelopersTab({ developers, loading }: DevelopersTabProps) {
  const [sortKey, setSortKey] = useState<SortKey>("spend_30d");
  const [sortAsc, setSortAsc] = useState(false);

  function handleSort(key: SortKey) {
    if (sortKey === key) {
      setSortAsc((v) => !v);
    } else {
      setSortKey(key);
      setSortAsc(false);
    }
  }

  const sorted = [...developers].sort((a, b) => {
    let aVal: string | number = a[sortKey] ?? "";
    let bVal: string | number = b[sortKey] ?? "";
    if (sortKey === "spend_30d") {
      aVal = Number(a.spend_30d);
      bVal = Number(b.spend_30d);
    }
    const cmp = aVal < bVal ? -1 : aVal > bVal ? 1 : 0;
    return sortAsc ? cmp : -cmp;
  });

  if (loading) {
    return (
      <div className="space-y-2 p-6">
        {Array.from({ length: 5 }).map((_, i) => (
          <div
            key={i}
            className="h-10 animate-pulse rounded"
            style={{ background: "#0F172A" }}
          />
        ))}
      </div>
    );
  }

  if (!developers.length) {
    return (
      <div className="flex flex-col items-center gap-2 py-16 text-center">
        <Users size={32} className="text-[#334155]" />
        <p className="text-sm text-[#64748B]">No developer activity yet.</p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-[#0F172A] bg-[#0F172A]">
            {COLUMNS.map(({ key, label }) => (
              <th
                key={key}
                onClick={() => handleSort(key)}
                className="cursor-pointer px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-[#64748B] transition-colors hover:text-[#94A3B8]"
              >
                <span className="flex items-center gap-1">
                  {label}
                  {sortKey === key ? (
                    sortAsc ? <ChevronUp size={11} /> : <ChevronDown size={11} />
                  ) : null}
                </span>
              </th>
            ))}
            <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-[#64748B]">
              Email
            </th>
          </tr>
        </thead>
        <tbody>
          {sorted.map((dev, i) => (
            <tr
              key={dev.user_id}
              className={`transition-colors hover:bg-[#334155]/20 ${
                i % 2 === 1 ? "bg-[#0F172A]" : ""
              }`}
            >
              <td className="px-6 py-3 font-medium text-[#F8FAFC]">{dev.name}</td>
              <td className="px-6 py-3 font-mono text-[#F8FAFC]">
                {fmtUsd(dev.spend_30d)}
              </td>
              <td className="px-6 py-3 text-[#94A3B8]">{fmtNum(dev.requests_30d)}</td>
              <td className="px-6 py-3 text-[#94A3B8]">{fmtTokens(dev.tokens_30d)}</td>
              <td className="px-6 py-3 text-[#94A3B8]">{fmtDate(dev.last_active)}</td>
              <td className="px-6 py-3 text-[#64748B]">{dev.email}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
