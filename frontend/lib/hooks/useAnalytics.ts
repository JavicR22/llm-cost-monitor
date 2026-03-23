import useSWR from "swr";
import { authedFetcher } from "@/lib/api";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface OverviewData {
  total_spend: string;
  total_requests: number;
  active_projects: number;
  active_developers: number;
  spend_trend_pct: number;
}

export interface ProjectAnalytics {
  id: string;
  name: string;
  spend_30d: string;
  requests_30d: number;
  teams_count: number;
  members_count: number;
  budget: string | null;
  budget_used_pct: number;
}

export interface TeamAnalytics {
  id: string;
  name: string;
  spend: string;
  requests: number;
  members_count: number;
}

export interface DeveloperAnalytics {
  user_id: string;
  name: string;
  email: string;
  spend_30d: string;
  requests_30d: number;
  tokens_30d: number;
  last_active: string | null;
}

export interface TimeseriesPoint {
  date: string;
  spend: string;
  requests: number;
}

export interface ModelUsage {
  model_name: string;
  spend: string;
  requests: number;
  tokens: number;
  pct_of_total: number;
}

export type Range = "7d" | "30d" | "90d";

// ---------------------------------------------------------------------------
// Hooks
// ---------------------------------------------------------------------------

export function useOverview(range: Range) {
  return useSWR<OverviewData>(
    `/api/v1/analytics/overview?range=${range}`,
    authedFetcher,
    { refreshInterval: 60_000 }
  );
}

export function useProjectsAnalytics(range: Range) {
  return useSWR<ProjectAnalytics[]>(
    `/api/v1/analytics/projects?range=${range}`,
    authedFetcher,
    { refreshInterval: 60_000 }
  );
}

export function useTeamsAnalytics(projectId: string, range: Range) {
  return useSWR<TeamAnalytics[]>(
    projectId ? `/api/v1/analytics/projects/${projectId}/teams?range=${range}` : null,
    authedFetcher,
    { refreshInterval: 60_000 }
  );
}

export function useDevelopersAnalytics(projectId: string, range: Range) {
  return useSWR<DeveloperAnalytics[]>(
    projectId
      ? `/api/v1/analytics/projects/${projectId}/developers?range=${range}`
      : null,
    authedFetcher,
    { refreshInterval: 60_000 }
  );
}

export function useTimeseries(range: Range, projectId?: string) {
  const url = projectId
    ? `/api/v1/analytics/spend/timeseries?range=${range}&project_id=${projectId}`
    : `/api/v1/analytics/spend/timeseries?range=${range}`;
  return useSWR<{ series: TimeseriesPoint[] }>(url, authedFetcher, {
    refreshInterval: 60_000,
  });
}

export function useModelsUsage(range: Range) {
  return useSWR<ModelUsage[]>(
    `/api/v1/analytics/models/usage?range=${range}`,
    authedFetcher,
    { refreshInterval: 60_000 }
  );
}
