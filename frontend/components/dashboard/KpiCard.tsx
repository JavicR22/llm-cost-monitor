import { cn } from "@/lib/utils";

interface KpiCardProps {
  label: string;
  value: string;
  change?: number | null;   // percentage, e.g. 12.0 or -8.0
  icon?: React.ReactNode;
  loading?: boolean;
}

export function KpiCard({ label, value, change, icon, loading }: KpiCardProps) {
  const isPositive = change !== null && change !== undefined && change > 0;
  const isNegative = change !== null && change !== undefined && change < 0;

  return (
    <div className="flex flex-1 flex-col gap-4 rounded-xl bg-[#1E293B] p-5">
      {/* Header row */}
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-[#94A3B8]">{label}</span>
        {icon && (
          <div
            className={cn(
              "flex h-7 w-7 items-center justify-center rounded-full",
              isNegative ? "bg-[#EF4444]/15" : "bg-[#10B981]/15"
            )}
          >
            {icon}
          </div>
        )}
      </div>

      {/* Value + change */}
      <div className="flex items-end gap-2">
        {loading ? (
          <div className="h-8 w-32 animate-pulse rounded bg-[#334155]" />
        ) : (
          <span className="text-2xl font-bold text-[#F8FAFC]">{value}</span>
        )}

        {!loading && change !== null && change !== undefined && (
          <span
            className={cn(
              "mb-0.5 text-xs font-medium",
              isPositive ? "text-[#F87171]" : isNegative ? "text-[#34D399]" : "text-[#64748B]"
            )}
          >
            {isPositive ? "+" : ""}
            {change.toFixed(1)}%
          </span>
        )}

        {!loading && (change === null || change === undefined) && (
          <span className="mb-0.5 text-xs text-[#64748B]">stable</span>
        )}
      </div>
    </div>
  );
}
