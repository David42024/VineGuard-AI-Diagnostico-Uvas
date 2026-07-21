"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Search,
  Activity,
  Leaf,
  Bug,
  Clock,
  Camera,
  Lightbulb,
  ArrowRight,
} from "lucide-react";
import { MetricCard } from "@/components/dashboard/metric-card";
import { useAuthStore } from "@/store/auth-store";
import { useTranslation } from "@/i18n";
import api from "@/lib/api";

export default function ClientDashboard() {
  const { user } = useAuthStore();
  const t = useTranslation();
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState<{
    totalDiagnostics: number;
    healthyPct: number;
    diseasedCount: number;
    lastResult: string;
  } | null>(null);

  const tips = [
    {
      icon: Camera,
      title: t("dashboard.tip1Title"),
      description: t("dashboard.tip1Desc"),
    },
    {
      icon: Lightbulb,
      title: t("dashboard.tip2Title"),
      description: t("dashboard.tip2Desc"),
    },
    {
      icon: Activity,
      title: t("dashboard.tip3Title"),
      description: t("dashboard.tip3Desc"),
    },
  ];

  useEffect(() => {
    api.get("/statistics/my-summary").then((res) => {
      const d = res.data;
      setStats({
        totalDiagnostics: d.total_diagnostics ?? 0,
        healthyPct: d.healthy_pct ?? 0,
        diseasedCount: Math.round((d.diseased_pct ?? 0) * (d.total_diagnostics ?? 0) / 100),
        lastResult: d.last_diagnosis?.result?.replace(/_/g, " ") || (d.today_diagnostics > 0 ? t("dashboard.today") : "—"),
      });
    }).catch(() => {
      setStats({ totalDiagnostics: 0, healthyPct: 0, diseasedCount: 0, lastResult: "—" });
    }).finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">
          {t("dashboard.welcome").replace("{name}", user?.name || t("dashboard.unknown"))}
        </h2>
        <p className="text-muted-foreground">
          {t("dashboard.subtitle")}
        </p>
      </div>

      {loading ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {[1, 2, 3, 4].map((i) => <Skeleton key={i} className="h-24 w-full" />)}
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <MetricCard
            title={t("dashboard.totalDiagnostics")}
            value={stats?.totalDiagnostics ?? 0}
            icon={Activity}
          />
          <MetricCard
            title={t("dashboard.healthyLeaves")}
            value={stats != null ? `${stats.healthyPct}%` : "0%"}
            icon={Leaf}
          />
          <MetricCard
            title={t("dashboard.diseasesDetected")}
            value={stats?.diseasedCount ?? 0}
            icon={Bug}
          />
          <MetricCard
            title={t("dashboard.lastResult")}
            value={stats?.lastResult ?? "—"}
            icon={Clock}
          />
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-2">
        <Card className="bg-gradient-to-br from-primary to-primary/80 text-primary-foreground">
          <CardContent className="p-8 flex flex-col items-center text-center space-y-4">
            <Search className="h-12 w-12" />
            <div>
              <h3 className="text-2xl font-bold">{t("dashboard.newDiagnosis")}</h3>
              <p className="text-primary-foreground/80 mt-1">
                {t("dashboard.newDiagnosisDesc")}
              </p>
            </div>
            <Link href="/dashboard/diagnosis">
              <Button
                variant="secondary"
                size="lg"
                className="mt-2"
              >
                {t("dashboard.start")}
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </Link>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <Camera className="h-5 w-5 text-primary" />
              {t("dashboard.photoTips")}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {tips.map((tip, i) => (
              <div key={i} className="flex gap-3">
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary/10">
                  <tip.icon className="h-4 w-4 text-primary" />
                </div>
                <div>
                  <p className="text-sm font-medium">{tip.title}</p>
                  <p className="text-xs text-muted-foreground">
                    {tip.description}
                  </p>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg">{t("dashboard.recentDiagnostics")}</CardTitle>
            <Link href="/dashboard/history">
              <Button variant="ghost" size="sm">
                {t("dashboard.viewAll")} <ArrowRight className="ml-1 h-4 w-4" />
              </Button>
            </Link>
          </div>
        </CardHeader>
        <CardContent>
          <RecentDiagnostics />
        </CardContent>
      </Card>
    </div>
  );
}

function RecentDiagnostics() {
  const t = useTranslation();
  const [items, setItems] = useState<Array<{ filename: string; result: string; date: string; confidence: string }>>([]);
  useEffect(() => {
    api.get("/diagnoses?limit=3").then((res) => {
      const list = (res.data?.items || []).map((d: { filename?: string; result: string; created_at?: string; confidence?: number }) => ({
        filename: d.filename || t("dashboard.unknown"),
        result: d.result?.replace(/_/g, " ") || "—",
        date: d.created_at ? new Date(d.created_at).toLocaleDateString() : "—",
        confidence: d.confidence != null ? `${(d.confidence * 100).toFixed(1)}%` : "—",
      }));
      setItems(list);
    }).catch(() => setItems([]));
  }, []);
  if (items.length === 0) {
    return <p className="text-sm text-muted-foreground text-center py-4">{t("dashboard.noRecentDiagnostics")}</p>;
  }
  return (
    <div className="space-y-4">
      {items.map((item, i) => (
        <div
          key={i}
          className="flex items-center justify-between rounded-lg border p-4"
        >
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-muted">
              <Leaf className="h-5 w-5 text-muted-foreground" />
            </div>
            <div>
              <p className="text-sm font-medium">{item.filename}</p>
              <p className="text-xs text-muted-foreground">{item.date}</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <Badge
              variant={
                item.result === "Healthy" ? "success" : "destructive"
              }
            >
              {item.result}
            </Badge>
            <span className="text-sm text-muted-foreground">
              {item.confidence}
            </span>
          </div>
        </div>
      ))}
    </div>
  );
}
