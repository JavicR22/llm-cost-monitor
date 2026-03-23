import useSWR from "swr";
import { authedFetcher, authedClient } from "@/lib/api";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface ServiceKey {
  id: string;
  label: string | null;
  key_prefix: string;
  is_active: boolean;
  created_at: string;
  last_used_at: string | null;
  project_id: string | null;
  team_id: string | null;
  owner_user_id: string | null;
}

export interface ServiceKeyCreated extends ServiceKey {
  raw_key: string; // shown once, never returned again
}

export interface ProviderKey {
  id: string;
  provider: string;
  key_prefix: string;
  label: string | null;
  is_active: boolean;
  created_at: string;
  last_validated_at: string | null;
}

export type ProviderName = "openai" | "anthropic" | "google" | "mistral";

// ---------------------------------------------------------------------------
// Hooks
// ---------------------------------------------------------------------------

export function useServiceKeys() {
  return useSWR<ServiceKey[]>("/api/v1/service-keys", authedFetcher, {
    refreshInterval: 30_000,
  });
}

export function useProviderKeys() {
  return useSWR<ProviderKey[]>("/api/v1/provider-keys", authedFetcher, {
    refreshInterval: 30_000,
  });
}

// ---------------------------------------------------------------------------
// Mutations
// ---------------------------------------------------------------------------

export async function createServiceKey(
  label?: string,
  projectId?: string | null
): Promise<ServiceKeyCreated> {
  return authedClient<ServiceKeyCreated>("/api/v1/service-keys", {
    method: "POST",
    body: JSON.stringify({
      label: label || null,
      project_id: projectId ?? null,
    }),
  });
}

export async function assignServiceKey(
  id: string,
  projectId: string | null,
  teamId: string | null = null,
  ownerUserId: string | null = null
): Promise<ServiceKey> {
  return authedClient<ServiceKey>(`/api/v1/service-keys/${id}/assign`, {
    method: "PATCH",
    body: JSON.stringify({
      project_id: projectId,
      team_id: teamId,
      owner_user_id: ownerUserId,
    }),
  });
}

export async function revokeServiceKey(id: string): Promise<ServiceKey> {
  return authedClient<ServiceKey>(`/api/v1/service-keys/${id}`, {
    method: "DELETE",
  });
}

export async function createProviderKey(
  provider: ProviderName,
  rawKey: string,
  label?: string
): Promise<ProviderKey> {
  return authedClient<ProviderKey>("/api/v1/provider-keys", {
    method: "POST",
    body: JSON.stringify({ provider, raw_key: rawKey, label: label || null }),
  });
}

export async function revokeProviderKey(id: string): Promise<ProviderKey> {
  return authedClient<ProviderKey>(`/api/v1/provider-keys/${id}`, {
    method: "DELETE",
  });
}
