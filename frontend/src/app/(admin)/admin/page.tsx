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
import { RefreshCw, Activity, Brain, Trophy } from "lucide-react";
import { formatDate } from "@/lib/utils";
import api from "@/lib/api";
import { ErrorState } from "@/components/feedback/error-state";

interface Diagnostic {
  id: number;
  created_at: string;
  filename: string;
  result: string;
  confidence: number;
  model_used: string;
  status: string;
  user_name?: string;
  username?: string;
}

interface UserInfo {
  id: number;
  username: string;
  name: string;
  role: string;
  active: boolean;
}

interface StatsData {
  totalDiagnostics: number;
  todayDiagnostics: number;
  healthyPercentage: number;
  diseasedPercentage: number;
  totalUsers: number;
  diseaseDistribution: { name: string; value: number; color: string }[];
  diagnosesByDate: { date: string; count: number }[];
  modelRanking: { name: string; accuracy: number; f1: number; recall: number; mcc: number }[];
  crossValidation: { modelo: string; accuracy_mean: number; accuracy_std: number }[];
}

const diseaseColors: Record<string, string> = {
  Healthy: "#22C55E",
  Black_rot: "#DC2626",
  Esca: "#F59E0B",
  Leaf_blight: "#3B82F6",
};

export default function AdminDashboard() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [stats, setStats] = useState<StatsData | null>(null);
  const [diagnostics, setDiagnostics] = useState<Diagnostic[]>([]);
  const [users, setUsers] = useState<UserInfo[]>([]);

  const fetchData = async () => {
    setLoading(true);
    setError("");
    try {
      const [statsRes, diagRes, usersRes] = await Promise.all([
        api.get("/statistics/summary").catch(() => ({ data: { general_stats: {}, disease_distribution: {}, diagnostics_by_date: [], ranking: [], cross_validation: [] } })),
        api.get("/diagnoses?limit=10").catch(() => ({ data: { items: [] } })),
        api.get("/users").catch(() => ({ data: [] })),
      ]);

      setDiagnostics(diagRes.data?.items || []);
      setUsers(usersRes.data || []);

      const s = statsRes.data;
      const g = s.general_stats || {};
      const dist = s.disease_distribution || {};

      const diseaseDistribution = Object.entries(dist).map(([name, value]) => ({
        name: name.replace(/_/g, " "),
        value: value as number,
        color: diseaseColors[name] || "#6B7280",
      }));

      const diagnosesByDate = (s.diagnostics_by_date || []).map(
        (d: { date: string; count: number }) => ({
          date: new Date(d.date).toLocaleDateString("es", {
            weekday: "short",
            day: "numeric",
            month: "short",
          }),
          count: d.count,
        })
      );

      const modelRanking = (s.ranking || []).map(
        (m: { modelo: string; accuracy: number; f1_score: number; recall: number; mcc?: number }) => ({
          name: m.modelo,
          accuracy: m.accuracy || 0,
          f1: m.f1_score || 0,
          recall: m.recall || 0,
          mcc: m.mcc || 0,
        })
      );

      const crossValidation = (s.cross_validation || []).map(
        (cv: { modelo: string; accuracy_mean: number; accuracy_std: number }) => ({
          modelo: cv.modelo,
          accuracy_mean: cv.accuracy_mean || 0,
          accuracy_std: cv.accuracy_std || 0,
        })
      );

      setStats({
        totalDiagnostics: g.total_diagnostics ?? 0,
        todayDiagnostics: g.today_diagnostics ?? 0,
        healthyPercentage: Math.round(g.healthy_pct ?? 0),
        diseasedPercentage: Math.round(g.diseased_pct ?? 0),
        totalUsers: g.total_users ?? 0,
        diseaseDistribution,
        diagnosesByDate,
        modelRanking,
        crossValidation,
      });
    } catch {
      setError("Error al cargar datos del dashboard");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  if (error) return <ErrorState message={error} onRetry={fetchData} />;
  const isEmpty = stats && stats.totalDiagnostics === 0;

  return (
    <div className="space-y-6">
      {/* Header */}
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

      {/* Métricas principales: 4 columnas responsive */}
      <StatsGrid data={stats ?? undefined} loading={loading} />

      {/* Tarjeta independiente: Mejor Modelo */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center gap-2">
            <Trophy className="h-5 w-5 text-yellow-500" />
            <CardTitle className="text-lg">Mejor Modelo</CardTitle>
          </div>
          <CardDescription>
            Seleccionado por mayor MCC ponderado con Accuracy y F1-macro
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <Skeleton className="h-16 w-full" />
          ) : stats?.modelRanking.length ? (
            <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:gap-8">
              <div>
                <p className="text-base font-bold">{stats.modelRanking[0].name}</p>
                <Badge variant="outline" className="mt-1 text-xs">Posición #1 en ranking</Badge>
              </div>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <p className="text-xs text-muted-foreground">Accuracy</p>
                  <p className="text-xl font-bold text-green-600">
                    {(stats.modelRanking[0].accuracy * 100).toFixed(2)}%
                  </p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">F1-macro</p>
                  <p className="text-xl font-bold text-primary">
                    {(stats.modelRanking[0].f1 * 100).toFixed(2)}%
                  </p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">MCC</p>
                  <p className="text-xl font-bold text-blue-600">
                    {stats.modelRanking[0].mcc
                      ? (stats.modelRanking[0].mcc * 100).toFixed(2) + "%"
                      : "N/A"}
                  </p>
                </div>
              </div>
              <details className="text-xs text-muted-foreground sm:ml-auto">
                <summary className="cursor-pointer select-none font-medium text-primary hover:underline">
                  Ver criterio de selección
                </summary>
                <p className="mt-2 max-w-xs leading-relaxed">
                  Se selecciona el modelo con el MCC más alto, ponderado junto con Accuracy y
                  F1-macro, garantizando robustez ante clases desbalanceadas.
                </p>
              </details>
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">Sin datos de ranking disponibles</p>
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
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Distribución de Enfermedades</CardTitle>
                <CardDescription>Proporción por clase diagnósticada</CardDescription>
              </CardHeader>
              <CardContent>
                {loading ? (
                  <Skeleton className="h-64 w-full" />
                ) : stats?.diseaseDistribution.length ? (
                  <DonutChart data={stats.diseaseDistribution} />
                ) : (
                  <p className="text-muted-foreground text-center py-12">Sin datos</p>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Diagnósticos por Día</CardTitle>
                <CardDescription>Últimos 30 días</CardDescription>
              </CardHeader>
              <CardContent>
                {loading ? (
                  <Skeleton className="h-64 w-full" />
                ) : stats?.diagnosesByDate.length ? (
                  <LineChart
                    data={stats.diagnosesByDate}
                    xKey="date"
                    lines={[{ key: "count", color: "#22C55E", name: "Diagnósticos" }]}
                  />
                ) : (
                  <p className="text-muted-foreground text-center py-12">Sin datos</p>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Ranking de Modelos</CardTitle>
                <CardDescription>Precisión y F1-Score</CardDescription>
              </CardHeader>
              <CardContent>
                {loading ? (
                  <Skeleton className="h-64 w-full" />
                ) : stats?.modelRanking.length ? (
                  <BarChart
                    data={stats.modelRanking.map((m) => ({
                      name: m.name.replace(/\(.*?\)/, "").trim(),
                      accuracy: +(m.accuracy * 100).toFixed(1),
                      f1: +(m.f1 * 100).toFixed(1),
                    }))}
                    xKey="name"
                    bars={[
                      { key: "accuracy", color: "#22C55E", name: "Precisión (%)" },
                      { key: "f1", color: "#166534", name: "F1 (%)" },
                    ]}
                  />
                ) : (
                  <p className="text-muted-foreground text-center py-12">Sin datos</p>
                )}
              </CardContent>
            </Card>
          </div>

          <div className="grid gap-6 md:grid-cols-2">
            {stats?.crossValidation && stats.crossValidation.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Validación Cruzada</CardTitle>
                  <CardDescription>Precisión media por modelo</CardDescription>
                </CardHeader>
                <CardContent>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Modelo</TableHead>
                        <TableHead>Precisión Media</TableHead>
                        <TableHead>Desviación Estándar</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {stats.crossValidation.map((cv) => (
                        <TableRow key={cv.modelo}>
                          <TableCell className="font-medium">{cv.modelo}</TableCell>
                          <TableCell>{(cv.accuracy_mean * 100).toFixed(2)}%</TableCell>
                          <TableCell>{(cv.accuracy_std * 100).toFixed(2)}%</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </CardContent>
              </Card>
            )}

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
                            <span>{u.name}</span>
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
                    <TableHead>Modelo</TableHead>
                    <TableHead>Predicción</TableHead>
                    <TableHead>Confianza</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {diagnostics.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={6} className="text-center text-muted-foreground py-8">
                        No hay diagnósticos recientes
                      </TableCell>
                    </TableRow>
                  ) : (
                    diagnostics.map((d) => (
                      <TableRow key={d.id}>
                        <TableCell className="font-medium text-sm">
                          {d.user_name || d.username || "—"}
                        </TableCell>
                        <TableCell className="text-sm max-w-[150px] truncate">{d.filename}</TableCell>
                        <TableCell className="text-sm whitespace-nowrap">
                          {d.created_at ? formatDate(new Date(d.created_at)) : "—"}
                        </TableCell>
                        <TableCell>
                          <Badge variant="outline" className="text-[10px]">
                            {d.model_used?.replace(/\(.*?\)/, "").trim() || "—"}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <Badge variant={d.result === "Healthy" ? "success" : "destructive"} className="text-[10px]">
                            {d.result.replace(/_/g, " ")}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-sm">
                          {d.confidence != null ? `${(d.confidence * 100).toFixed(1)}%` : "—"}
                        </TableCell>
                      </TableRow>
                    ))
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
