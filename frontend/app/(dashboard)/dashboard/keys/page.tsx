"use client";

import { ServiceKeysList } from "@/components/keys/ServiceKeysList";
import { ProviderKeysList } from "@/components/keys/ProviderKeysList";

export default function KeysPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-[#F8FAFC]">API Keys</h1>
        <p className="mt-1 text-sm text-[#94A3B8]">
          Manage service keys for your clients and encrypted provider keys for LLM forwarding.
        </p>
      </div>

      <div className="flex flex-col gap-6">
        <ServiceKeysList />
        <ProviderKeysList />
      </div>
    </div>
  );
}
