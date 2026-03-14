import useSWR from "swr";
import { authedFetcher, authedClient } from "@/lib/api";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type AlertRuleType = "budget_soft" | "budget_hard" | "anomaly" | "circuit_breaker";
export type AlertScope = "hourly" | "daily" | "monthly";
export type AlertSeverity = "info" | "warning" | "critical";
export type AlertEventType = "soft_limit" | "hard_limit" | "anomaly" | "circuit_breaker";

export interface AlertRule {
  id: string;
  organization_id: string;
  type: AlertRuleType;
  scope: AlertScope;
  threshold_value: string | null;
  anomaly_multiplier: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface AlertEvent {
  id: string;
  organization_id: string;
  alert_rule_id: string | null;
  severity: AlertSeverity;
  type: AlertEventType;
  message: string;
  triggered_value: string;
  threshold_value: string;
  notification_sent: boolean;
  created_at: string;
}

export interface CircuitBreakerStatus {
  is_open: boolean;
}

export interface CreateRulePayload {
  type: AlertRuleType;
  scope: AlertScope;
  threshold_value?: string;
  anomaly_multiplier?: string;
  is_active?: boolean;
}

// ---------------------------------------------------------------------------
// Hooks
// ---------------------------------------------------------------------------

export function useAlertRules() {
  return useSWR<AlertRule[]>("/api/v1/alerts/rules", authedFetcher, {
    refreshInterval: 30_000,
  });
}

export function useAlertEvents(limit = 50, offset = 0) {
  return useSWR<AlertEvent[]>(
    `/api/v1/alerts/events?limit=${limit}&offset=${offset}`,
    authedFetcher,
    { refreshInterval: 20_000 }
  );
}

export function useCircuitBreaker() {
  return useSWR<CircuitBreakerStatus>(
    "/api/v1/alerts/circuit-breaker",
    authedFetcher,
    { refreshInterval: 10_000 }
  );
}

// ---------------------------------------------------------------------------
// Mutations
// ---------------------------------------------------------------------------

export async function createAlertRule(payload: CreateRulePayload): Promise<AlertRule> {
  return authedClient<AlertRule>("/api/v1/alerts/rules", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function toggleAlertRule(
  id: string,
  is_active: boolean
): Promise<AlertRule> {
  return authedClient<AlertRule>(`/api/v1/alerts/rules/${id}`, {
    method: "PATCH",
    body: JSON.stringify({ is_active }),
  });
}

export async function deleteAlertRule(id: string): Promise<void> {
  return authedClient<void>(`/api/v1/alerts/rules/${id}`, { method: "DELETE" });
}

export async function unlockCircuitBreaker(): Promise<CircuitBreakerStatus> {
  return authedClient<CircuitBreakerStatus>(
    "/api/v1/alerts/circuit-breaker/unlock",
    { method: "POST" }
  );
}
