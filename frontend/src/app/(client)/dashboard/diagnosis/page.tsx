"use client";

import { useState, useEffect } from "react";
import { UploadZone } from "@/components/diagnosis/upload-zone";
import { ResultCard } from "@/components/diagnosis/result-card";
import { ConsensusView } from "@/components/diagnosis/consensus-view";
import { ComparisonView } from "@/components/diagnosis/comparison-view";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { toast } from "sonner";
import {
  Search,
  Brain,
  Star,
  GitBranch,
  LayoutDashboard,
  Loader2,
  Download,
  RotateCcw,
  FileWarning,
  AlertTriangle,
} from "lucide-react";
import api from "@/lib/api";
import type { DiagnosisResponse, ModelRanking } from "@/types/api";

type ModelKey = "consensus" | "best_model" | "compare_all";

interface ModeOption {
  key: ModelKey;
  icon: typeof Brain;
  label: string;
  description: string;
}

const MODES: ModeOption[] = [
  {
    key: "consensus",
    icon: GitBranch,
    label: "Consenso",
    description: "Combina resultados de múltiples modelos",
  },
  {
    key: "best_model",
    icon: Star,
    label: "Mejor Modelo",
    description: "Usa el modelo con mejor rendimiento",
  },
  {
    key: "compare_all",
    icon: LayoutDashboard,
    label: "Comparar Todos",
    description: "Ejecuta todos los modelos y compara sus predicciones",
  },
];

export default function DiagnosisPage() {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string>("");
  const [modelKey, setModelKey] = useState<ModelKey>("consensus");
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [result, setResult] = useState<DiagnosisResponse | null>(null);
  const [error, setError] = useState("");
  const [modelRanking, setModelRanking] = useState<ModelRanking[]>([]);

  useEffect(() => {
    api.get<ModelRanking[]>("/models/ranking")
      .then((res) => setModelRanking(res.data))
      .catch(() => {});
  }, []);

  const handleFileSelect = (selectedFile: File) => {
    setFile(selectedFile);
    setPreview(URL.createObjectURL(selectedFile));
    setResult(null);
    setError("");
  };

  const handleRemove = () => {
    setFile(null);
    if (preview) URL.revokeObjectURL(preview);
    setPreview("");
    setResult(null);
    setError("");
  };

  const handleAnalyze = async () => {
    if (!file) return;
    setLoading(true);
    setProgress(0);
    setError("");

    const interval = setInterval(() => {
      setProgress((p) => Math.min(p + 10, 90));
    }, 500);

    try {
      let key: string;
      if (modelKey === "best_model") {
        key = "best_model";
      } else if (modelKey === "compare_all") {
        key = "all";
      } else {
        key = "consensus";
      }

      const formData = new FormData();
      formData.append("file", file);
      formData.append("model_key", key);

      const response = await api.post<DiagnosisResponse>("/diagnoses", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setResult(response.data);
      toast.success("Diagnóstico completado exitosamente");
    } catch (err) {
      const msg =
        err instanceof Error ? err.message : "Error al procesar la imagen. Intente nuevamente.";
      setError(msg);
      toast.error(msg);
    } finally {
      clearInterval(interval);
      setProgress(100);
      setLoading(false);
    }
  };

  const [downloading, setDownloading] = useState(false);
  type ReportFormat = "docx" | "pdf" | "xlsx";
  const [reportFormat, setReportFormat] = useState<ReportFormat>("docx");

const handleDownload = async () => {
    if (!result) return;
    setDownloading(true);

    try {
      const genRes = await api.post<{ download_url: string; filename: string }>(
        `/reports/diagnosis/${result.id}`,
        { format: reportFormat }
      );

      const origin = new URL(api.defaults.baseURL as string).origin;

      const fileRes = await api.get(genRes.data.download_url, {
        baseURL: origin,
        responseType: "blob",
      });

      const blob = new Blob([fileRes.data]);
      const blobUrl = window.URL.createObjectURL(blob);

      const link = document.createElement("a");
      link.href = blobUrl;
      link.download = genRes.data.filename || `reporte_${result.id}.${reportFormat}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(blobUrl);

      toast.success("Reporte descargado");
    } catch {
      toast.error("No se pudo generar el reporte. Intenta de nuevo.");
    } finally {
      setDownloading(false);
    }
  };

  return (
    <div className="space-y-6 max-w-4xl">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">
          Nuevo Diagnóstico
        </h2>
        <p className="text-muted-foreground">
          Sube una imagen de hoja de vid para analizarla con nuestros modelos de
          IA
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">1. Subir Imagen</CardTitle>
            </CardHeader>
            <CardContent>
              <UploadZone
                onFileSelect={handleFileSelect}
                selectedFile={file}
                preview={preview}
                onRemove={handleRemove}
              />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-lg">2. Seleccionar Modo</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid gap-3">
                {MODES.map((mode) => {
                  const Icon = mode.icon;
                  const selected = modelKey === mode.key;
                  return (
                    <button
                      key={mode.key}
                      onClick={() => setModelKey(mode.key)}
                      className={`flex items-center gap-4 rounded-lg border p-4 text-left transition-colors ${
                        selected
                          ? "border-primary bg-primary/5"
                          : "hover:border-muted-foreground/30"
                      }`}
                    >
                      <div
                        className={`flex h-10 w-10 items-center justify-center rounded-full ${
                          selected
                            ? "bg-primary text-primary-foreground"
                            : "bg-muted"
                        }`}
                      >
                        <Icon className="h-5 w-5" />
                      </div>
                      <div className="flex-1">
                        <p className="text-sm font-medium">{mode.label}</p>
                        <p className="text-xs text-muted-foreground">
                          {mode.description}
                        </p>
                      </div>
                      {selected && (
                        <Badge variant="success">Seleccionado</Badge>
                      )}
                    </button>
                  );
                })}
              </div>
            </CardContent>
          </Card>

          <Button
            size="lg"
            className="w-full"
            disabled={!file || loading}
            onClick={handleAnalyze}
          >
            {loading ? (
              <>
                <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                Analizando...
              </>
            ) : (
              <>
                <Search className="mr-2 h-5 w-5" />
                Analizar hoja
              </>
            )}
          </Button>

          {loading && (
            <div className="space-y-2">
              <Progress value={progress} />
              <p className="text-center text-sm text-muted-foreground">
                Procesando imagen... {progress}%
              </p>
            </div>
          )}

          {error && (
            <div className="flex items-center gap-2 rounded-md bg-destructive/10 p-4 text-sm text-destructive">
              <AlertTriangle className="h-4 w-4" />
              {error}
            </div>
          )}
        </div>

        <div className="space-y-6">
          {result && (
            <>
              <ResultCard diagnosis={result} />
              {(modelKey === "consensus" || modelKey === "compare_all") && result.consensus && (
                <ConsensusView consensus={result.consensus} />
              )}
              {modelKey === "compare_all" && result.predictions && result.predictions.length > 0 && (
                <ComparisonView
                  predictions={result.predictions}
                  consensusClass={result.consensus?.predicted_class}
                  ranking={modelRanking}
                />
              )}

              <Card>
                <CardContent className="p-4">
                  <div className="flex items-start gap-2 rounded-md bg-muted p-3 text-xs text-muted-foreground">
                    <FileWarning className="mt-0.5 h-4 w-4 shrink-0" />
                    <span>
                      Este resultado es una estimación generada por inteligencia
                      artificial y no reemplaza la evaluación de un ingeniero
                      agrónomo o especialista fitosanitario.
                    </span>
                  </div>
                </CardContent>
              </Card>

              <div className="flex gap-3">
                <select
                  value={reportFormat}
                  onChange={(e) => setReportFormat(e.target.value as ReportFormat)}
                  className="rounded-md border px-3 py-2 text-sm"
                >
                  <option value="docx">Word (.docx)</option>
                  <option value="pdf">PDF</option>
                  <option value="xlsx">Excel (.xlsx)</option>
                </select>

                <Button
                  variant="outline"
                  className="flex-1"
                  onClick={handleDownload}
                  disabled={downloading}
                >
                  <Download className="mr-2 h-4 w-4" />
                  {downloading ? "Generando..." : "Descargar Reporte"}
                </Button>
                <Button variant="outline" className="flex-1" onClick={handleRemove}>
                  <RotateCcw className="mr-2 h-4 w-4" />
                  Nuevo Análisis
                </Button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
