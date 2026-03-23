import useSWR from "swr";
import { authedFetcher, authedClient } from "@/lib/api";

export interface NotificationChannel {
  id: string;
  type: string;
  display_hint: string;
  is_active: boolean;
  created_at: string;
}

export function useNotificationChannels() {
  return useSWR<NotificationChannel[]>(
    "/api/v1/notification-channels",
    authedFetcher,
    { refreshInterval: 30_000 }
  );
}

export async function addNotificationChannel(email: string): Promise<NotificationChannel> {
  return authedClient<NotificationChannel>("/api/v1/notification-channels", {
    method: "POST",
    body: JSON.stringify({ type: "email", email }),
  });
}

export async function removeNotificationChannel(id: string): Promise<void> {
  return authedClient<void>(`/api/v1/notification-channels/${id}`, {
    method: "DELETE",
  });
}
