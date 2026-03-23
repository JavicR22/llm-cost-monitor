"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import useSWR from "swr";
import { authedFetcher } from "@/lib/api";

interface MeResponse {
  id: string;
  role: string;
}

interface RoleGuardProps {
  allowedRoles: string[];
  children: React.ReactNode;
}

export function RoleGuard({ allowedRoles, children }: RoleGuardProps) {
  const router = useRouter();
  const { data: me, isLoading } = useSWR<MeResponse>(
    "/api/v1/auth/me",
    authedFetcher
  );

  useEffect(() => {
    if (!me) return;
    if (!allowedRoles.includes(me.role)) {
      router.replace("/dashboard");
    }
  }, [me, allowedRoles, router]);

  if (isLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-[#3B82F6] border-t-transparent" />
      </div>
    );
  }

  if (!me || !allowedRoles.includes(me.role)) {
    return null;
  }

  return <>{children}</>;
}
