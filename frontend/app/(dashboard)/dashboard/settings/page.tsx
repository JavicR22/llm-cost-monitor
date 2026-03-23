"use client";

import { useState } from "react";
import { Bell, User } from "lucide-react";
import { NotificationsTab } from "@/components/settings/NotificationsTab";

type Tab = "notifications" | "profile";

const TABS: { key: Tab; label: string; icon: React.ReactNode }[] = [
  { key: "notifications", label: "Notifications", icon: <Bell size={15} /> },
  { key: "profile",       label: "Profile",        icon: <User size={15} /> },
];

export default function SettingsPage() {
  const [tab, setTab] = useState<Tab>("notifications");

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-[#F8FAFC]">Settings</h1>
        <p className="mt-1 text-sm text-[#94A3B8]">
          Manage your organization preferences and integrations.
        </p>
      </div>

      {/* Tab bar */}
      <div
        className="flex gap-1 rounded-xl p-1"
        style={{ background: "#0F172A", border: "1px solid #334155" }}
      >
        {TABS.map(({ key, label, icon }) => (
          <button
            key={key}
            onClick={() => setTab(key)}
            className="flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition-colors"
            style={{
              background: tab === key ? "#1E293B" : "transparent",
              color: tab === key ? "#F8FAFC" : "#64748B",
              border: tab === key ? "1px solid #334155" : "1px solid transparent",
            }}
          >
            {icon}
            {label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      {tab === "notifications" && <NotificationsTab />}

      {tab === "profile" && (
        <div
          className="rounded-xl p-8 text-center"
          style={{ background: "#1E293B", border: "1px solid #334155" }}
        >
          <p className="text-sm text-[#64748B]">Profile settings coming soon.</p>
        </div>
      )}
    </div>
  );
}
