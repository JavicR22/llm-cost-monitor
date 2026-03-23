"use client";

import { ActivityRow } from "@/lib/hooks/useDashboard";
import { cn } from "@/lib/utils";

interface ActivityTableProps {
  items: ActivityRow[];
  total: number;
  page: number;
  pageSize: number;
  loading?: boolean;
  onPageChange: (page: number) => void;
}

function fmtUsd(v: number | string) {
  return `$${Number(v).toFixed(6)}`;
}

function fmtTime(iso: string) {
  return new Date(iso).toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function fmtTokens(n: number) {
  if (n >= 1000) return `${(n / 1000).toFixed(1)}k`;
  return String(n);
}

const COLS = ["Model", "Input", "Output", "Cost", "Latency", "Type", "Time"];

export function ActivityTable({
  items,
  total,
  page,
  pageSize,
  loading,
  onPageChange,
}: ActivityTableProps) {
  const totalPages = Math.ceil(total / pageSize);
  const from = (page - 1) * pageSize + 1;
  const to = Math.min(page * pageSize, total);

  return (
    <div className="overflow-hidden rounded-xl bg-[#1E293B]">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-[#0F172A] bg-[#0F172A] px-6 py-4">
        <h3 className="text-base font-semibold text-[#F8FAFC]">Recent Activity</h3>
        <button className="text-xs font-medium text-[#60A5FA] hover:text-[#3B82F6]">
          Download CSV
        </button>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-[#0F172A] bg-[#0F172A]">
              {COLS.map((col) => (
                <th
                  key={col}
                  className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-[#64748B]"
                >
                  {col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {loading
              ? Array.from({ length: 5 }).map((_, i) => (
                  <tr key={i} className={i % 2 === 1 ? "bg-[#0F172A]" : ""}>
                    {COLS.map((c) => (
                      <td key={c} className="px-6 py-3">
                        <div className="h-4 animate-pulse rounded bg-[#334155]" />
                      </td>
                    ))}
                  </tr>
                ))
              : items.map((row, i) => (
                  <tr
                    key={row.id}
                    className={cn(
                      "transition-colors hover:bg-[#334155]/30",
                      i % 2 === 1 && "bg-[#0F172A]"
                    )}
                  >
                    <td className="px-6 py-3 font-medium text-[#F8FAFC]">
                      {row.display_name}
                    </td>
                    <td className="px-6 py-3 text-[#94A3B8]">
                      {fmtTokens(row.tokens_input)}
                    </td>
                    <td className="px-6 py-3 text-[#94A3B8]">
                      {fmtTokens(row.tokens_output)}
                    </td>
                    <td className="px-6 py-3 font-mono text-[#F8FAFC]">
                      {fmtUsd(row.cost_usd)}
                    </td>
                    <td className="px-6 py-3 text-[#94A3B8]">{row.latency_ms}ms</td>
                    <td className="px-6 py-3">
                      <span
                        className={cn(
                          "rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase",
                          row.is_streaming
                            ? "bg-[#8B5CF6]/15 text-[#A78BFA]"
                            : "bg-[#3B82F6]/15 text-[#60A5FA]"
                        )}
                      >
                        {row.is_streaming ? "stream" : "sync"}
                      </span>
                    </td>
                    <td className="px-6 py-3 text-[#64748B]">
                      {fmtTime(row.created_at)}
                    </td>
                  </tr>
                ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div className="flex items-center justify-between border-t border-[#0F172A] bg-[#0F172A] px-6 py-4">
        <span className="text-xs text-[#64748B]">
          {total === 0
            ? "No results"
            : `Showing ${from} to ${to} of ${total} results`}
        </span>
        <div className="flex items-center gap-2">
          <button
            onClick={() => onPageChange(page - 1)}
            disabled={page <= 1}
            className="rounded-lg bg-[#1E293B] px-3 py-1.5 text-xs font-medium text-[#94A3B8] transition-colors hover:bg-[#334155] disabled:opacity-40"
          >
            Previous
          </button>

          {/* Page numbers — show up to 5 */}
          <div className="flex items-center gap-1">
            {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
              const p = totalPages <= 5 ? i + 1 : Math.max(1, page - 2) + i;
              if (p > totalPages) return null;
              return (
                <button
                  key={p}
                  onClick={() => onPageChange(p)}
                  className={cn(
                    "flex h-7 w-7 items-center justify-center rounded-md text-xs font-medium transition-colors",
                    p === page
                      ? "bg-[#3B82F6] text-white"
                      : "text-[#94A3B8] hover:bg-[#334155]"
                  )}
                >
                  {p}
                </button>
              );
            })}
          </div>

          <button
            onClick={() => onPageChange(page + 1)}
            disabled={page >= totalPages}
            className="rounded-lg bg-[#1E293B] px-3 py-1.5 text-xs font-medium text-[#94A3B8] transition-colors hover:bg-[#334155] disabled:opacity-40"
          >
            Next
          </button>
        </div>
      </div>
    </div>
  );
}
