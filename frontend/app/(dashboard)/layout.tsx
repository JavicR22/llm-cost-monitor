"use client";

import { useEffect } from "react";
import { useRouter, usePathname } from "next/navigation";
import useSWR from "swr";
import { Sidebar } from "@/components/layout/Sidebar";
import { TopBar } from "@/components/layout/TopBar";
import { authedFetcher } from "@/lib/api";

interface MeResponse {
  id: string;
  name: string;
  email: string;
  role: string;
  org_id: string;
  assigned_project_id: string | null;
  assigned_team_id: string | null;
  has_seen_key_modal: boolean;
  last_login_at: string | null;
}

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const pathname = usePathname();

  const { data: me } = useSWR<MeResponse>("/api/v1/auth/me", authedFetcher);

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (!token) {
      router.replace("/login");
      return;
    }
  }, [router]);

  useEffect(() => {
    if (!me) return;

    const isDeveloperPath = pathname === "/dashboard/developer";
    const isAdminRestrictedPath =
      pathname.startsWith("/dashboard/keys") || pathname.startsWith("/dashboard/members");

    if (me.role === "developer" && !isDeveloperPath) {
      router.replace("/dashboard/developer");
    } else if (me.role !== "developer" && isDeveloperPath) {
      router.replace("/dashboard");
    } else if (me.role === "admin" && isAdminRestrictedPath) {
      router.replace("/dashboard");
    }
  }, [me, pathname, router]);

  return (
    <div className="flex h-screen overflow-hidden bg-[#0F172A]">
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-hidden bg-[#1E293B]">
        <TopBar />
        <main className="flex-1 overflow-y-auto p-8">{children}</main>
      </div>
    </div>
  );
}
