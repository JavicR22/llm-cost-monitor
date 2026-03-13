import useSWR from "swr";
import { authedFetcher } from "@/lib/api";

export interface SummaryData {
  total_spend_usd: number;
  request_count: number;
  avg_cost_per_request: number;
  total_tokens: number;
  spend_change_pct: number | null;
  request_change_pct: number | null;
}

export interface DailySpend {
  date: string;
  spend_usd: number;
  request_count: number;
}

export interface SpendByModel {
  model_name: string;
  display_name: string;
  spend_usd: number;
  request_count: number;
  total_tokens: number;
  pct_of_total: number;
}

export interface ActivityRow {
  id: string;
  model_name: string;
  display_name: string;
  tokens_input: number;
  tokens_output: number;
  cost_usd: number;
  latency_ms: number;
  is_streaming: boolean;
  created_at: string;
}

export interface ActivityData {
  items: ActivityRow[];
  total: number;
  page: number;
  page_size: number;
}

export function useSummary(days: number) {
  return useSWR<SummaryData>(
    `/api/v1/dashboard/summary?days=${days}`,
    authedFetcher,
    { refreshInterval: 30_000 }
  );
}

export function useSpendOverTime(days: number) {
  return useSWR<DailySpend[]>(
    `/api/v1/dashboard/spend-over-time?days=${days}`,
    authedFetcher,
    { refreshInterval: 60_000 }
  );
}

export function useSpendByModel(days: number) {
  return useSWR<SpendByModel[]>(
    `/api/v1/dashboard/spend-by-model?days=${days}`,
    authedFetcher,
    { refreshInterval: 60_000 }
  );
}

export function useActivity(page: number, pageSize = 10) {
  return useSWR<ActivityData>(
    `/api/v1/dashboard/activity?page=${page}&page_size=${pageSize}`,
    authedFetcher,
    { refreshInterval: 30_000 }
  );
}
