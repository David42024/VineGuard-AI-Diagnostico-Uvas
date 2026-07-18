"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Brain, RefreshCw, Star, AlertCircle } from "lucide-react";
import { ErrorState } from "@/components/feedback/error-state";
import { modelsApi } from "@/lib/api";
import type { ModelInfo, ModelRanking } from "@/lib/api";

function formatPct(val: number | undefined | null): string {
  return val != null ? `${(val * 100).toFixed(1)}%` : "N/A";
}

function getStatusLabel(status: string): string {
  const labels: Record<string, string> = {
    available: "Disponible",
    unavailable: "No disponible",
    loaded: "Disponible",
    training: "Entrenando",
    pending: "Pendiente",
    error: "Error",
    not_loaded: "No disponible",
  };
  return labels[status] || status;
}

function getStatusVariant(status: string): "success" | "warning" | "secondary" | "destructive" {
  if (status === "available" || status === "loaded" || status === "production") return "success";
  if (status === "training" || status === "staging") return "warning";
  if (status === "error" || status === "unavailable") return "secondary";
  return "secondary";
}

function getTypeLabel(type: string): string {
  return type;
}

export default function ModelsPage() {
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [ranking, setRanking] = useState<ModelRanking[]>([]);
  const [bestName, setBestName] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const fetchData = async () => {
    setLoading(true);
    setError("");
    try {
      const [modelList, rankList, best] = await Promise.all([
        modelsApi.list(),
        modelsApi.getRanking().catch(() => []),
        modelsApi.getBest().catch(() => null),
      ]);
      setModels(modelList);
      setRanking(rankList);
      setBestName(best?.model_name ?? "");
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Error al cargar modelos");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  if (error) return <ErrorState message={error} onRetry={fetchData} />;

  const bestModel = models.find(
    (m) => bestName && (m.name === bestName || m.id === bestName)
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">
            Gestión de Modelos
          </h2>
          <p className="text-muted-foreground">
            Visualiza y gestiona los modelos de IA disponibles
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={fetchData} disabled={loading}>
          <RefreshCw className={`mr-2 h-4 w-4 ${loading ? "animate-spin" : ""}`} />
          Cargar modelos
        </Button>
      </div>

      {loading && models.length === 0 && (
        <div className="flex items-center justify-center py-12 text-muted-foreground">
          <RefreshCw className="mr-2 h-5 w-5 animate-spin" />
          Cargando modelos...
        </div>
      )}

      {!loading && models.length === 0 && !error && (
        <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
          <AlertCircle className="mb-2 h-8 w-8" />
          <p>No hay modelos disponibles. Ejecuta los entrenamientos desde Streamlit.</p>
        </div>
      )}

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {models.map((model) => {
          const isBest = bestModel?.id === model.id;
          const m = model.metrics;
          return (
            <Card key={model.id} className="relative overflow-hidden">
              {isBest && (
                <div className="absolute right-2 top-2">
                  <Badge variant="success" className="gap-1">
                    <Star className="h-3 w-3" />
                    Mejor
                  </Badge>
                </div>
              )}
              <CardHeader>
                <div className="flex items-center gap-2">
                  <Brain className="h-5 w-5 text-primary" />
                  <CardTitle className="text-lg">{model.name}</CardTitle>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex gap-2">
                  <Badge variant="secondary">{getTypeLabel(model.type)}</Badge>
                  <Badge variant={getStatusVariant(model.status)}>
                    {getStatusLabel(model.status)}
                  </Badge>
                </div>
                {m ? (
                  <div className="space-y-2">
                    {m.accuracy != null && (
                      <div className="flex justify-between text-sm">
                        <span className="text-muted-foreground">Accuracy</span>
                        <span className="font-medium">{formatPct(m.accuracy)}</span>
                      </div>
                    )}
                    {m.f1_score != null && (
                      <div className="flex justify-between text-sm">
                        <span className="text-muted-foreground">F1-score</span>
                        <span className="font-medium">{formatPct(m.f1_score)}</span>
                      </div>
                    )}
                    {m.recall != null && (
                      <div className="flex justify-between text-sm">
                        <span className="text-muted-foreground">Recall</span>
                        <span className="font-medium">{formatPct(m.recall)}</span>
                      </div>
                    )}
                    {m.precision != null && (
                      <div className="flex justify-between text-sm">
                        <span className="text-muted-foreground">Precision</span>
                        <span className="font-medium">{formatPct(m.precision)}</span>
                      </div>
                    )}
                    {m.mcc != null && (
                      <div className="flex justify-between text-sm">
                        <span className="text-muted-foreground">MCC</span>
                        <span className="font-medium">{m.mcc.toFixed(4)}</span>
                      </div>
                    )}
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground">Sin métricas</p>
                )}
              </CardContent>
            </Card>
          );
        })}
      </div>

      {ranking.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Ranking de Modelos</CardTitle>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>#</TableHead>
                  <TableHead>Modelo</TableHead>
                  <TableHead>Tipo</TableHead>
                  <TableHead>Accuracy</TableHead>
                  <TableHead>F1-score</TableHead>
                  <TableHead>MCC</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {ranking.map((row, index) => (
                  <TableRow key={index}>
                    <TableCell className="font-medium">{row.ranking}</TableCell>
                    <TableCell>{row.modelo}</TableCell>
                    <TableCell>
                      {models.find((m) => row.modelo.includes(m.name) || m.name.includes(row.modelo))?.type
                        ? getTypeLabel(models.find((m) => row.modelo.includes(m.name) || m.name.includes(row.modelo))!.type)
                        : "—"}
                    </TableCell>
                    <TableCell>{formatPct(row.accuracy)}</TableCell>
                    <TableCell>{formatPct(row.f1_score)}</TableCell>
                    <TableCell>{row.mcc?.toFixed(4) ?? "N/A"}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
