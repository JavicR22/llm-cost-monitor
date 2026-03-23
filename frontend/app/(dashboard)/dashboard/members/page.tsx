"use client";

import { useState } from "react";
import useSWR from "swr";
import { UserPlus } from "lucide-react";
import { authedFetcher } from "@/lib/api";
import { useMembers } from "@/lib/hooks/useFinOps";
import { InviteForm } from "@/components/members/InviteForm";
import { MemberRow } from "@/components/members/MemberRow";

interface MeResponse {
  id: string;
  role: string;
}

function TableSkeleton() {
  return (
    <>
      {Array.from({ length: 4 }).map((_, i) => (
        <tr key={i} className="border-b border-[#0F172A]">
          {Array.from({ length: 5 }).map((_, j) => (
            <td key={j} className="px-6 py-4">
              <div className="h-4 animate-pulse rounded bg-[#334155]" />
            </td>
          ))}
        </tr>
      ))}
    </>
  );
}

export default function MembersPage() {
  const { data: me } = useSWR<MeResponse>("/api/v1/auth/me", authedFetcher);
  const { data: members, isLoading, mutate } = useMembers();
  const [showInvite, setShowInvite] = useState(false);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-[#F8FAFC]">Team Members</h1>
          <p className="mt-1 text-sm text-[#94A3B8]">
            Manage who has access to your organization.
          </p>
        </div>
        {(me?.role === "owner" || me?.role === "admin") && (
          <button
            onClick={() => setShowInvite((v) => !v)}
            className="flex items-center gap-2 rounded-lg bg-[#3B82F6] px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-[#2563EB]"
          >
            <UserPlus size={16} />
            Invite Member
          </button>
        )}
      </div>

      {/* Inline invite form */}
      {showInvite && (
        <InviteForm
          onCreated={() => {
            mutate();
            setShowInvite(false);
          }}
          onCancel={() => setShowInvite(false)}
        />
      )}

      {/* Table */}
      <div className="overflow-hidden rounded-xl bg-[#1E293B]" style={{ border: "1px solid #334155" }}>
        <div className="border-b border-[#0F172A] bg-[#0F172A] px-6 py-4">
          <h3 className="text-base font-semibold text-[#F8FAFC]">
            Members
            {members && (
              <span className="ml-2 text-sm font-normal text-[#64748B]">
                ({members.length})
              </span>
            )}
          </h3>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-[#0F172A] bg-[#0F172A]">
                {["Name", "Email", "Role", "Last Login", ""].map((col) => (
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
              {isLoading ? (
                <TableSkeleton />
              ) : (members ?? []).length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-6 py-12 text-center text-sm text-[#64748B]">
                    No members found.
                  </td>
                </tr>
              ) : (
                (members ?? []).map((member) => (
                  <MemberRow
                    key={member.id}
                    member={member}
                    isSelf={member.id === me?.id}
                    callerRole={me?.role ?? "viewer"}
                    onMutate={() => mutate()}
                  />
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
