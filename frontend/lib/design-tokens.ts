export const colors = {
  bg: {
    primary: "#0F172A",    // deep navy — main background
    secondary: "#1E293B",  // cards, sidebar, inputs
    tertiary: "#334155",   // borders, hover states
  },
  accent: {
    blue: "#3B82F6",
    blueHover: "#2563EB",
  },
  status: {
    success: "#10B981",
    warning: "#F59E0B",
    danger: "#EF4444",
    info: "#3B82F6",
  },
  text: {
    primary: "#F8FAFC",
    secondary: "#94A3B8",
    muted: "#64748B",
  },
  providers: {
    openai: "#3B82F6",
    anthropic: "#F97316",
    google: "#10B981",
    mistral: "#8B5CF6",
  },
} as const;

export const spacing = {
  card: { padding: "24px", borderRadius: "12px", border: "1px solid #334155" },
  sidebar: { width: "240px" },
  topbar: { height: "64px" },
  content: { padding: "32px" },
} as const;
