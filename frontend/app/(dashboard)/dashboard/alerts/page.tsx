"use client";

import { CircuitBreakerPanel } from "@/components/alerts/CircuitBreakerPanel";
import { AlertRulesList } from "@/components/alerts/AlertRulesList";
import { AlertEventsTable } from "@/components/alerts/AlertEventsTable";

export default function AlertsPage() {
  return (
    <div className="space-y-6">
      {/* Page header */}
      <div>
        <h1 className="text-2xl font-semibold text-[#F8FAFC]">Alerts</h1>
        <p className="mt-1 text-sm text-[#94A3B8]">
          Configure budget limits, anomaly detection, and circuit breakers.
        </p>
      </div>

      {/* Circuit Breaker status */}
      <CircuitBreakerPanel />

      {/* Rules + Events */}
      <div className="flex gap-6">
        <div className="flex-[2]">
          <AlertRulesList />
        </div>
        <div className="flex-[3]">
          <AlertEventsTable />
        </div>
      </div>
    </div>
  );
}
