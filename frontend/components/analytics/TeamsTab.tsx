"use client";

import { Users } from "lucide-react";
import type { TeamAnalytics } from "@/lib/hooks/useAnalytics";

interface TeamsTabProps {
  teams: TeamAnalytics[];
  loading: boolean;
}

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

function RelativeBar({ value, max }: { value: number; max: number }) {
  const pct = max > 0 ? (value / max) * 100 : 0;
  return (
    <div className="mt-2 h-1 w-full overflow-hidden rounded-full bg-[#334155]">
      <div
        className="h-full rounded-full"
        style={{ width: `${pct}%`, background: "#3B82F6" }}
      />
    </div>
  );
}

export function TeamsTab({ teams, loading }: TeamsTabProps) {
  if (loading) {
    return (
      <div className="grid grid-cols-3 gap-4 p-6">
        {Array.from({ length: 3 }).map((_, i) => (
          <div
            key={i}
            className="h-28 animate-pulse rounded-xl"
            style={{ background: "#0F172A" }}
          />
        ))}
      </div>
    );
  }

  if (!teams.length) {
    return (
      <div className="flex flex-col items-center gap-2 py-16 text-center">
        <Users size={32} className="text-[#334155]" />
        <p className="text-sm text-[#64748B]">No teams in this project yet.</p>
      </div>
    );
  }

  const maxSpend = Math.max(...teams.map((t) => Number(t.spend)));

  return (
    <div className="grid grid-cols-3 gap-4 p-6">
      {teams.map((team) => (
        <div
          key={team.id}
          className="rounded-xl px-5 py-4"
          style={{ background: "#0F172A", border: "1px solid #334155" }}
        >
          <div className="flex items-start justify-between gap-2">
            <p className="font-medium text-[#F8FAFC]">{team.name}</p>
            <span className="shrink-0 text-xs text-[#64748B]">
              {team.members_count} members
            </span>
          </div>
          <p className="mt-2 text-lg font-semibold text-[#60A5FA]">
            {fmtUsd(team.spend)}
          </p>
          <p className="text-xs text-[#64748B]">{fmtNum(team.requests)} requests</p>
          <RelativeBar value={Number(team.spend)} max={maxSpend} />
        </div>
      ))}
    </div>
  );
}
