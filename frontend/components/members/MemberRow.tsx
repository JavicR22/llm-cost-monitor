"use client";

import { useState } from "react";
import { Trash2 } from "lucide-react";
import { OrgMember, updateMemberRole, deleteMember } from "@/lib/hooks/useFinOps";

const ROLE_BADGE: Record<string, { label: string; color: string }> = {
  owner: { label: "Owner", color: "#3B82F6" },
  admin: { label: "Admin", color: "#10B981" },
  viewer: { label: "Viewer", color: "#64748B" },
};

function fmtDate(iso: string | null | undefined) {
  if (!iso) return "Never";
  return new Date(iso).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
}

interface Props {
  member: OrgMember;
  isSelf: boolean;
  callerRole: string;
  onMutate: () => void;
}

export function MemberRow({ member, isSelf, callerRole, onMutate }: Props) {
  const [roleLoading, setRoleLoading] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const badge = ROLE_BADGE[member.role] ?? { label: member.role, color: "#64748B" };

  const canChangeRole =
    !isSelf && callerRole === "owner" && member.role !== "owner";

  const canDelete =
    !isSelf &&
    (callerRole === "owner" || (callerRole === "admin" && member.role !== "owner"));

  async function handleRoleChange(newRole: string) {
    setRoleLoading(true);
    try {
      await updateMemberRole(member.id, newRole);
      onMutate();
    } catch {
      // silently surface nothing; toast pattern not set up yet
    } finally {
      setRoleLoading(false);
    }
  }

  async function handleDelete() {
    if (!confirm(`Remove ${member.name} from the organization?`)) return;
    setDeleting(true);
    try {
      await deleteMember(member.id);
      onMutate();
    } finally {
      setDeleting(false);
    }
  }

  return (
    <tr
      className={`border-b border-[#0F172A] transition-colors hover:bg-[#334155]/20 ${
        isSelf ? "bg-[#3B82F6]/5" : ""
      }`}
    >
      {/* Name */}
      <td className="px-6 py-4">
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[#334155] text-xs font-semibold text-[#F8FAFC]">
            {member.name.charAt(0).toUpperCase()}
          </div>
          <div>
            <p className="text-sm font-medium text-[#F8FAFC]">
              {member.name}
              {isSelf && (
                <span className="ml-2 text-xs font-normal text-[#64748B]">(you)</span>
              )}
            </p>
          </div>
        </div>
      </td>

      {/* Email */}
      <td className="px-6 py-4 text-sm text-[#94A3B8]">{member.email}</td>

      {/* Role */}
      <td className="px-6 py-4">
        <span
          className="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium"
          style={{ backgroundColor: `${badge.color}22`, color: badge.color }}
        >
          {badge.label}
        </span>
      </td>

      {/* Last login */}
      <td className="px-6 py-4 text-sm text-[#64748B]">
        {fmtDate(member.last_login_at)}
      </td>

      {/* Actions */}
      <td className="px-6 py-4 text-right">
        <div className="flex items-center justify-end gap-2">
          {canChangeRole && (
            <select
              disabled={roleLoading}
              value={member.role}
              onChange={(e) => handleRoleChange(e.target.value)}
              className="rounded-lg border border-[#334155] bg-[#0F172A] px-2 py-1 text-xs text-[#94A3B8] focus:border-[#3B82F6] focus:outline-none disabled:opacity-50"
            >
              <option value="viewer">Viewer</option>
              <option value="admin">Admin</option>
            </select>
          )}
          {canDelete && (
            <button
              onClick={handleDelete}
              disabled={deleting}
              className="rounded p-1 text-[#64748B] transition-colors hover:text-[#EF4444] disabled:opacity-40"
              title="Remove member"
            >
              <Trash2 size={14} />
            </button>
          )}
          {!canChangeRole && !canDelete && (
            <span className="text-xs text-[#334155]">—</span>
          )}
        </div>
      </td>
    </tr>
  );
}
