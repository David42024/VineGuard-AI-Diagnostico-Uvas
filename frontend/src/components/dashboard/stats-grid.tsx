"use client";

import { Activity, Bug, Leaf, CalendarDays } from "lucide-react";
import { MetricCard } from "./metric-card";
import { Skeleton } from "@/components/ui/skeleton";
import { useTranslation } from "@/i18n";

interface StatsData {
  totalDiagnostics: number;
  todayDiagnostics: number;
  healthyPercentage: number;
  diseasedPercentage: number;
  totalUsers?: number;
}

interface StatsGridProps {
  data?: StatsData;
  loading?: boolean;
}

export function StatsGrid({ data, loading }: StatsGridProps) {
  const t = useTranslation();

  if (loading) {
    return (
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} className="h-[140px] rounded-lg" />
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
      <MetricCard
        title={t("dashboard.totalDiagnostics")}
        value={data?.totalDiagnostics ?? 0}
        icon={Activity}
      />
      <MetricCard
        title={t("dashboard.today")}
        value={data?.todayDiagnostics ?? 0}
        icon={CalendarDays}
        description={t("dashboard.todayDiagnoses")}
      />
      <MetricCard
        title={t("dashboard.healthyLeaves")}
        value={`${data?.healthyPercentage ?? 0}%`}
        icon={Leaf}
      />
      <MetricCard
        title={t("dashboard.diseasedLeaves")}
        value={`${data?.diseasedPercentage ?? 0}%`}
        icon={Bug}
      />
    </div>
  );
}
