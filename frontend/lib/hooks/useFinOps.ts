import useSWR from "swr";
import { authedFetcher, authedClient } from "@/lib/api";

// ------------------------------------------------------------------
// Org members (for owner_user_id assignment)
// ------------------------------------------------------------------

export interface OrgMember {
  id: string;
  name: string;
  email: string;
  role: string;
  last_login_at: string | null;
}

export function useMembers() {
  return useSWR<OrgMember[]>("/api/v1/members", authedFetcher, {
    refreshInterval: 60_000,
  });
}

export async function inviteMember(data: {
  name: string;
  email: string;
  password: string;
  role: string;
}): Promise<OrgMember> {
  return authedClient<OrgMember>("/api/v1/members/invite", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function updateMemberRole(id: string, role: string): Promise<OrgMember> {
  return authedClient<OrgMember>(`/api/v1/members/${id}/role`, {
    method: "PATCH",
    body: JSON.stringify({ role }),
  });
}

export async function deleteMember(id: string): Promise<void> {
  await authedClient<void>(`/api/v1/members/${id}`, { method: "DELETE" });
}

// ------------------------------------------------------------------
// Types
// ------------------------------------------------------------------

export interface Project {
  id: string;
  name: string;
  description: string | null;
  budget_limit: string | null;
  created_at: string;
}

export interface Team {
  id: string;
  project_id: string;
  name: string;
  budget_limit: string | null;
  created_at: string;
}

export interface ProjectSpend {
  project_id: string;
  project_name: string;
  budget_limit: string | null;
  total_cost: string;
  total_tokens: number;
  requests: number;
  period?: string;
}

export interface TeamSpend {
  team_id: string;
  team_name: string;
  total_cost: string;
  total_tokens: number;
  requests: number;
  period?: string;
}

export interface MemberSpend {
  user_id: string;
  user_name: string;
  user_email: string;
  total_cost: string;
  total_tokens: number;
  requests: number;
  period?: string;
}

export type GroupBy = "day" | "week" | "month";

// ------------------------------------------------------------------
// Projects
// ------------------------------------------------------------------

export function useProjects() {
  return useSWR<Project[]>("/api/v1/projects", authedFetcher, {
    refreshInterval: 30_000,
  });
}

export async function createProject(data: {
  name: string;
  description?: string;
  budget_limit?: number;
}): Promise<Project> {
  return authedClient<Project>("/api/v1/projects", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function updateProject(
  id: string,
  data: { name?: string; description?: string; budget_limit?: number }
): Promise<Project> {
  return authedClient<Project>(`/api/v1/projects/${id}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export async function deleteProject(id: string): Promise<void> {
  await authedClient<void>(`/api/v1/projects/${id}`, { method: "DELETE" });
}

// ------------------------------------------------------------------
// Teams
// ------------------------------------------------------------------

export function useTeams(projectId: string) {
  return useSWR<Team[]>(
    projectId ? `/api/v1/projects/${projectId}/teams` : null,
    authedFetcher,
    { refreshInterval: 30_000 }
  );
}

export async function createTeam(
  projectId: string,
  data: { name: string; budget_limit?: number }
): Promise<Team> {
  return authedClient<Team>(`/api/v1/projects/${projectId}/teams`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function deleteTeam(
  projectId: string,
  teamId: string
): Promise<void> {
  await authedClient<void>(`/api/v1/projects/${projectId}/teams/${teamId}`, {
    method: "DELETE",
  });
}

// ------------------------------------------------------------------
// Reports
// ------------------------------------------------------------------

export function useProjectsSpend(
  from: string,
  to: string,
  groupBy: GroupBy = "day"
) {
  return useSWR<ProjectSpend[]>(
    from && to
      ? `/api/v1/reports/projects?from=${from}&to=${to}&group_by=${groupBy}`
      : null,
    authedFetcher,
    { refreshInterval: 60_000 }
  );
}

export function useTeamsSpend(
  projectId: string,
  from: string,
  to: string,
  groupBy: GroupBy = "day"
) {
  return useSWR<TeamSpend[]>(
    projectId && from && to
      ? `/api/v1/reports/projects/${projectId}/teams?from=${from}&to=${to}&group_by=${groupBy}`
      : null,
    authedFetcher,
    { refreshInterval: 60_000 }
  );
}

export function useMembersSpend(
  projectId: string,
  from: string,
  to: string,
  groupBy: GroupBy = "day"
) {
  return useSWR<MemberSpend[]>(
    projectId && from && to
      ? `/api/v1/reports/projects/${projectId}/members?from=${from}&to=${to}&group_by=${groupBy}`
      : null,
    authedFetcher,
    { refreshInterval: 60_000 }
  );
}

export function useSummaryReport(from: string, to: string) {
  return useSWR<ProjectSpend[]>(
    from && to ? `/api/v1/reports/summary?from=${from}&to=${to}` : null,
    authedFetcher,
    { refreshInterval: 60_000 }
  );
}
