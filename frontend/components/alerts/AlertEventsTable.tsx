"use client";

import { useState } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { useAlertEvents, type AlertEvent } from "@/lib/hooks/useAlerts";

const PAGE_SIZE = 10;

const SEVERITY_STYLE: Record<string, { bg: string; color: string }> = {
  critical: { bg: "#ef444420", color: "#ef4444" },
  warning:  { bg: "#f59e0b20", color: "#f59e0b" },
  info:     { bg: "#3b82f620", color: "#3b82f6" },
};

const TYPE_LABEL: Record<string, string> = {
  soft_limit:      "Soft Limit",
  hard_limit:      "Hard Limit",
  anomaly:         "Anomaly",
  circuit_breaker: "Circuit Breaker",
};

function fmtDate(iso: string) {
  return new Intl.DateTimeFormat("en-US", {
    month: "short", day: "numeric",
    hour: "2-digit", minute: "2-digit",
  }).format(new Date(iso));
}

function EventRow({ event }: { event: AlertEvent }) {
  const sev = SEVERITY_STYLE[event.severity] ?? SEVERITY_STYLE.info;

  return (
    <tr className="border-t border-[#334155] transition-colors hover:bg-[#334155]/30">
      <td className="px-4 py-3">
        <span
          className="rounded px-2 py-0.5 text-[11px] font-semibold"
          style={{ background: sev.bg, color: sev.color }}
        >
          {event.severity.toUpperCase()}
        </span>
      </td>
      <td className="px-4 py-3 text-xs text-[#94A3B8]">
        {TYPE_LABEL[event.type] ?? event.type}
      </td>
      <td className="max-w-[260px] px-4 py-3 text-xs text-[#F8FAFC]">
        <p className="truncate">{event.message}</p>
      </td>
      <td className="px-4 py-3 text-xs text-[#64748B]">{fmtDate(event.created_at)}</td>
      <td className="px-4 py-3">
        {event.notification_sent ? (
          <span className="text-[10px] text-[#10B981]">Sent</span>
        ) : (
          <span className="text-[10px] text-[#64748B]">—</span>
        )}
      </td>
    </tr>
  );
}

export function AlertEventsTable() {
  const [offset, setOffset] = useState(0);
  const { data: events, isLoading } = useAlertEvents(PAGE_SIZE, offset);

  const page = Math.floor(offset / PAGE_SIZE) + 1;
  const hasPrev = offset > 0;
  const hasNext = (events?.length ?? 0) === PAGE_SIZE;

  return (
    <div
      className="flex flex-col rounded-xl"
      style={{ background: "#1E293B", border: "1px solid #334155" }}
    >
      {/* Header */}
      <div className="border-b border-[#334155] px-5 py-4">
        <h2 className="text-sm font-semibold text-[#F8FAFC]">Event History</h2>
        <p className="text-xs text-[#64748B]">Recent alert events, newest first</p>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-[#334155]">
              {["Severity", "Type", "Message", "Time", "Notified"].map((h) => (
                <th
                  key={h}
                  className="px-4 py-2.5 text-left text-[11px] font-medium uppercase tracking-wide text-[#64748B]"
                >
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              Array.from({ length: 5 }).map((_, i) => (
                <tr key={i} className="border-t border-[#334155]">
                  {Array.from({ length: 5 }).map((_, j) => (
                    <td key={j} className="px-4 py-3">
                      <div className="h-3 w-3/4 animate-pulse rounded" style={{ background: "#334155" }} />
                    </td>
                  ))}
                </tr>
              ))
            ) : events?.length === 0 ? (
              <tr>
                <td colSpan={5} className="py-10 text-center text-sm text-[#64748B]">
                  No alert events recorded yet.
                </td>
              </tr>
            ) : (
              events?.map((ev) => <EventRow key={ev.id} event={ev} />)
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div className="flex items-center justify-between border-t border-[#334155] px-5 py-3">
        <span className="text-xs text-[#64748B]">Page {page}</span>
        <div className="flex gap-1">
          <button
            onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}
            disabled={!hasPrev}
            className="rounded p-1 text-[#94A3B8] transition-colors hover:bg-[#334155] disabled:opacity-30"
          >
            <ChevronLeft size={15} />
          </button>
          <button
            onClick={() => setOffset(offset + PAGE_SIZE)}
            disabled={!hasNext}
            className="rounded p-1 text-[#94A3B8] transition-colors hover:bg-[#334155] disabled:opacity-30"
          >
            <ChevronRight size={15} />
          </button>
        </div>
      </div>
    </div>
  );
}
