"use client";

import { useState, useEffect } from "react";
import { StatsGrid } from "@/components/dashboard/stats-grid";
import { DonutChart } from "@/components/charts/donut-chart";
import { BarChart } from "@/components/charts/bar-chart";
import { LineChart } from "@/components/charts/line-chart";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { RefreshCw, Activity, Trophy, Users } from "lucide-react";
import { formatDate, formatConfidence } from "@/lib/formatters";
import api from "@/lib/api";
import type { ModelRanking, BestModelResponse } from "@/types/api";
import { ErrorState } from "@/components/feedback/error-state";
import { formatClassName, MODEL_NAMES, MODE_LABELS } from "@/lib/constants";

interface RecentDiagnostic {
  id: number;
  created_at: string;
  filename: string;
  result: string;
  confidence: number;
  model_used: string;
  analysis_type: string;
  status: string;
  user_name?: string;
  username?: string;
}

interface SystemUser {
  id: number;
  username: string;
  name: string;
  role: string;
  active: boolean;
  created_at?: string;
}

interface SummaryData {
  general_stats: {
    total_diagnostics: number;
    today_diagnostics: number;
    healthy_pct: number;
    diseased_pct: number;
    total_users: number;
  };
  disease_distribution: Record<string, number>;
  diagnostics_by_date: { date: string; count: number }[];
  ranking: ModelRanking[];
  cross_validation: Record<string, string>[];
  best_model: BestModelResponse | null;
}

const DISEASE_COLORS: Record<string, string> = {
  Healthy: "#22C55E",
  Black_rot: "#DC2626",
  Esca: "#F59E0B",
  Leaf_blight: "#3B82F6",
};

function getModeLabel(modelUsed: string, analysisType?: string): { mode: string; model: string } {
  const at = analysisType || "";
  if (at === "consensus" || modelUsed === "consensus")
    return { mode: "Consenso", model: "5 modelos" };
  if (at === "best_model" || modelUsed === "best_model" || modelUsed === "H1")
    return { mode: "Mejor modelo", model: MODEL_NAMES[modelUsed] || modelUsed };
  if (at === "all" || modelUsed === "all")
    return { mode: "Comparación", model: "Todos los modelos" };
  return { mode: MODEL_NAMES[modelUsed] || modelUsed, model: modelUsed };
}

export default function AdminDashboard() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [summary, setSummary] = useState<SummaryData | null>(null);
  const [bestModel, setBestModel] = useState<BestModelResponse | null>(null);
  const [diagnostics, setDiagnostics] = useState<RecentDiagnostic[]>([]);
  const [users, setUsers] = useState<SystemUser[]>([]);

  const fetchData = async () => {
    setLoading(true);
    setError("");
    try {
      const [summaryRes, diagRes, usersRes] = await Promise.all([
        api.get("/statistics/summary").catch(() => ({ data: null })),
        api.get("/diagnoses?limit=10").catch(() => ({ data: { items: [] } })),
        api.get("/users").catch(() => ({ data: [] })),
      ]);

      const s = summaryRes.data;
      setSummary(s);
      setBestModel(s?.best_model || null);
      setDiagnostics(diagRes.data?.items || []);
      setUsers(usersRes.data || []);
    } catch {
      setError("Error al cargar datos del dashboard");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, []);

  if (error) return <ErrorState message={error} onRetry={fetchData} />;

  const stats = summary?.general_stats;
  const isEmpty = stats && stats.total_diagnostics === 0;
  const diseaseDist = summary?.disease_distribution
    ? Object.entries(summary.disease_distribution).map(([name, value]) => ({
        name: formatClassName(name),
        value,
        color: DISEASE_COLORS[name] || "#6B7280",
      }))
    : [];

  const totalDiagnostics = stats?.total_diagnostics ?? 0;
  const distTotal = diseaseDist.reduce((s, d) => s + d.value, 0);
  const healthyCount = diseaseDist.find((d) => d.name === "Healthy")?.value ?? 0;
  const diseasedCount = distTotal - healthyCount;
  const healthyPct = totalDiagnostics > 0 ? (healthyCount / totalDiagnostics) * 100 : 0;
  const diseasedPct = totalDiagnostics > 0 ? (diseasedCount / totalDiagnostics) * 100 : 0;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Panel de Administración</h2>
          <p className="text-muted-foreground">Resumen general del sistema VineGuard AI</p>
        </div>
        <Button variant="outline" size="sm" onClick={fetchData} disabled={loading}>
          <RefreshCw className={`mr-2 h-4 w-4 ${loading ? "animate-spin" : ""}`} />
          Actualizar
        </Button>
      </div>

      <StatsGrid
        data={
          stats
            ? {
                totalDiagnostics,
                todayDiagnostics: stats.today_diagnostics,
                healthyPercentage: Math.round(healthyPct),
                diseasedPercentage: Math.round(diseasedPct),
                totalUsers: stats.total_users,
              }
            : undefined
        }
        loading={loading}
      />

      {/* Best Model — from models/modelo_final.json */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center gap-2">
            <Trophy className="h-5 w-5 text-yellow-500" />
            <CardTitle className="text-lg">Mejor Modelo</CardTitle>
          </div>
          {bestModel?.criterio_seleccion ? (
            <CardDescription>{bestModel.criterio_seleccion.join("; ")}</CardDescription>
          ) : (
            <CardDescription>Seleccionado por mayor MCC; en caso de empate, se prioriza F1-macro y luego Accuracy</CardDescription>
          )}
        </CardHeader>
        <CardContent>
          {loading && !bestModel ? (
            <Skeleton className="h-16 w-full" />
          ) : bestModel && bestModel.modelo_ganador ? (
            <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:gap-8">
              <div>
                <p className="text-base font-bold">{bestModel.modelo_ganador}</p>
                <Badge variant="outline" className="mt-1 text-xs">Posición #1 en ranking</Badge>
              </div>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <p className="text-xs text-muted-foreground">Accuracy</p>
                  <p className="text-xl font-bold text-green-600">
                    {bestModel.metricas_test?.accuracy != null
                      ? `${(bestModel.metricas_test.accuracy * 100).toFixed(2)}%`
                      : "N/A"}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">F1-macro</p>
                  <p className="text-xl font-bold text-primary">
                    {bestModel.metricas_test?.f1_macro != null
                      ? `${(bestModel.metricas_test.f1_macro * 100).toFixed(2)}%`
                      : "N/A"}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">MCC</p>
                  <p className="text-xl font-bold text-blue-600">
                    {bestModel.metricas_test?.mcc != null
                      ? `${(bestModel.metricas_test.mcc * 100).toFixed(2)}%`
                      : "N/A"}
                  </p>
                </div>
              </div>
              {bestModel.victorias_significativas_holm != null && (
                <p className="text-sm text-muted-foreground">
                  {bestModel.victorias_significativas_holm} victorias significativas con corrección Holm
                </p>
              )}
              {bestModel.requiere_reentrenamiento != null && (
                <p className={`text-xs font-medium ${bestModel.requiere_reentrenamiento ? "text-amber-600" : "text-green-600"}`}>
                  {bestModel.requiere_reentrenamiento
                    ? "⚠ Requiere reentrenamiento"
                    : "✅ Modelo persistido y listo para inferencia"}
                </p>
              )}
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">
              Sin datos de ranking disponibles. Ejecuta src/seleccion_mejor_modelo.py.
            </p>
          )}
        </CardContent>
      </Card>

      {isEmpty ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-16 text-muted-foreground">
            <Activity className="h-16 w-16 mb-4 opacity-30" />
            <p className="text-xl font-medium">No hay datos disponibles</p>
            <p className="text-sm mt-1">Realiza diagnósticos para ver estadísticas</p>
          </CardContent>
        </Card>
      ) : (
        <>
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {/* Disease Distribution */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Distribución de Enfermedades</CardTitle>
                <CardDescription>Proporción por clase diagnosticada</CardDescription>
              </CardHeader>
              <CardContent>
                {loading ? (
                  <Skeleton className="h-64 w-full" />
                ) : diseaseDist.length ? (
                  <>
                    <DonutChart data={diseaseDist} />
                    {distTotal !== totalDiagnostics && (
                      <p className="text-xs text-amber-600 mt-2 text-center">
                        Advertencia: suma de clases ({distTotal}) no coincide con total ({totalDiagnostics})
                      </p>
                    )}
                  </>
                ) : (
                  <p className="text-muted-foreground text-center py-12">Sin datos</p>
                )}
              </CardContent>
            </Card>

            {/* Diagnoses by Day */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Diagnósticos por Día</CardTitle>
                <CardDescription>Últimos 30 días</CardDescription>
              </CardHeader>
              <CardContent>
                {loading ? (
                  <Skeleton className="h-64 w-full" />
                ) : summary?.diagnostics_by_date?.length ? (
                  <LineChart
                    data={summary.diagnostics_by_date.map((d) => ({
                      date: new Date(d.date).toLocaleDateString("es", {
                        weekday: "short", day: "numeric", month: "short",
                      }),
                      count: d.count,
                    }))}
                    xKey="date"
                    lines={[{ key: "count", color: "#22C55E", name: "Diagnósticos" }]}
                  />
                ) : (
                  <p className="text-muted-foreground text-center py-12">Sin datos</p>
                )}
              </CardContent>
            </Card>

            {/* Ranking */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Ranking de Modelos</CardTitle>
                <CardDescription>MCC, F1-macro y Accuracy sobre TEST</CardDescription>
              </CardHeader>
              <CardContent>
                {loading ? (
                  <Skeleton className="h-64 w-full" />
                ) : summary?.ranking?.length ? (
                  <BarChart
                    data={summary.ranking.map((m) => ({
                      name: m.modelo.replace(/\(.*?\)/, "").trim(),
                      mcc: +(m.mcc * 100).toFixed(1),
                      f1: +((m.f1_macro ?? m.f1_score ?? 0) * 100).toFixed(1),
                      accuracy: +(m.accuracy * 100).toFixed(1),
                    }))}
                    xKey="name"
                    bars={[
                      { key: "mcc", color: "#2563EB", name: "MCC (%)" },
                      { key: "f1", color: "#166534", name: "F1 (%)" },
                      { key: "accuracy", color: "#22C55E", name: "Accuracy (%)" },
                    ]}
                  />
                ) : (
                  <p className="text-muted-foreground text-center py-12">Sin datos</p>
                )}
              </CardContent>
            </Card>
          </div>

          <div className="grid gap-6 md:grid-cols-2">
            {/* Cross Validation */}
            {summary?.cross_validation && summary.cross_validation.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Validación Cruzada</CardTitle>
                  <CardDescription>Métricas sobre los modelos entrenados con validación cruzada (5 folds)</CardDescription>
                </CardHeader>
                <CardContent>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Modelo</TableHead>
                        <TableHead>Accuracy media</TableHead>
                        <TableHead>F1-macro media</TableHead>
                        <TableHead>MCC media</TableHead>
                        <TableHead>N° folds</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {summary.cross_validation.map((cv: Record<string, string>, i: number) => (
                        <TableRow key={i}>
                          <TableCell className="font-medium">{cv.modelo || `Modelo ${i + 1}`}</TableCell>
                          <TableCell>
                            {cv.accuracy_mean != null
                              ? `${(parseFloat(cv.accuracy_mean) * 100).toFixed(2)}%`
                              : "—"}
                          </TableCell>
                          <TableCell>
                            {cv.f1_macro_mean != null
                              ? `${(parseFloat(cv.f1_macro_mean) * 100).toFixed(2)}%`
                              : "—"}
                          </TableCell>
                          <TableCell>
                            {cv.mcc_mean != null
                              ? `${(parseFloat(cv.mcc_mean) * 100).toFixed(2)}%`
                              : "—"}
                          </TableCell>
                          <TableCell>{cv.n_folds || "—"}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </CardContent>
              </Card>
            )}

            {/* Users */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Usuarios del Sistema</CardTitle>
                <CardDescription>Resumen de cuentas activas</CardDescription>
              </CardHeader>
              <CardContent>
                {loading ? (
                  <Skeleton className="h-48 w-full" />
                ) : users.length === 0 ? (
                  <p className="text-muted-foreground text-center py-8">Sin datos</p>
                ) : (
                  <div className="space-y-3">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">Total usuarios</span>
                      <span className="font-bold text-lg">{users.length}</span>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">Administradores</span>
                      <span className="font-bold">{users.filter((u) => u.role === "admin").length}</span>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">Clientes</span>
                      <span className="font-bold">{users.filter((u) => u.role === "client").length}</span>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">Activos</span>
                      <span className="font-bold text-green-600">{users.filter((u) => u.active).length}</span>
                    </div>
                    <div className="border-t pt-2 mt-2">
                      <p className="text-xs text-muted-foreground mb-2">Últimos usuarios:</p>
                      <div className="space-y-1.5">
                        {users.slice(0, 4).map((u) => (
                          <div key={u.id} className="flex items-center justify-between text-sm">
                            <div className="flex items-center gap-2">
                              <Users className="h-3 w-3 text-muted-foreground" />
                              <span>{u.name}</span>
                            </div>
                            <Badge variant={u.role === "admin" ? "default" : "secondary"} className="text-[10px]">
                              {u.role === "admin" ? "Admin" : "Cliente"}
                            </Badge>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Recent Diagnostics */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Diagnósticos Recientes</CardTitle>
              <CardDescription>Últimos 10 diagnósticos del sistema</CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Usuario</TableHead>
                    <TableHead>Archivo</TableHead>
                    <TableHead>Fecha</TableHead>
                    <TableHead>Modo</TableHead>
                    <TableHead>Modelo</TableHead>
                    <TableHead>Predicción</TableHead>
                    <TableHead>Confianza</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {diagnostics.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={7} className="text-center text-muted-foreground py-8">
                        No hay diagnósticos recientes
                      </TableCell>
                    </TableRow>
                  ) : (
                    diagnostics.map((d) => {
                      const modeInfo = getModeLabel(d.model_used, d.analysis_type);
                      return (
                        <TableRow key={d.id}>
                          <TableCell className="font-medium text-sm">
                            {d.user_name || d.username || "—"}
                          </TableCell>
                          <TableCell className="text-sm max-w-[120px] truncate" title={d.filename}>
                            {d.filename}
                          </TableCell>
                          <TableCell className="text-sm whitespace-nowrap">
                            {d.created_at ? formatDate(new Date(d.created_at)) : "—"}
                          </TableCell>
                          <TableCell>
                            <Badge variant="outline" className="text-[10px]">{modeInfo.mode}</Badge>
                          </TableCell>
                          <TableCell className="text-sm text-muted-foreground">{modeInfo.model}</TableCell>
                          <TableCell>
                            <Badge
                              variant={d.result === "Healthy" ? "success" : "destructive"}
                              className="text-[10px]"
                            >
                              {formatClassName(d.result)}
                            </Badge>
                          </TableCell>
                          <TableCell className="text-sm">
                            {d.confidence != null ? formatConfidence(d.confidence) : "—"}
                          </TableCell>
                        </TableRow>
                      );
                    })
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
