"use client";

import { useState } from "react";
import { UploadZone } from "@/components/diagnosis/upload-zone";
import { ResultCard } from "@/components/diagnosis/result-card";
import { ConsensusView } from "@/components/diagnosis/consensus-view";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
import { toast } from "sonner";
import {
  Search,
  Brain,
  GitBranch,
  Cpu,
  Loader2,
  Download,
  RotateCcw,
  FileWarning,
  AlertTriangle,
} from "lucide-react";
import api from "@/lib/api";
import type { Diagnosis } from "@/lib/api";

type ModelKey = "consensus" | "modelo_svm" | "modelo_rf" | "modelo_cnn" | "modelo_ensemble" | "modelo_resnet";

export default function DiagnosisPage() {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string>("");
  const [modelKey, setModelKey] = useState<ModelKey>("consensus");
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [result, setResult] = useState<Diagnosis | null>(null);
  const [error, setError] = useState("");

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
      const formData = new FormData();
      formData.append("file", file);
      formData.append("model_key", modelKey);

      const response = await api.post<Diagnosis>("/diagnosis", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setResult(response.data);
      toast.success("Diagnóstico completado exitosamente");
    } catch {
      setError("Error al procesar la imagen. Intente nuevamente.");
      toast.error("Error al realizar el diagnóstico");
    } finally {
      clearInterval(interval);
      setProgress(100);
      setLoading(false);
    }
  };

  const handleDownload = () => {
    toast.success("Reporte descargado");
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
                <button
                  onClick={() => setModelKey("consensus")}
                  className={`flex items-center gap-4 rounded-lg border p-4 text-left transition-colors ${
                    modelKey === "consensus"
                      ? "border-primary bg-primary/5"
                      : "hover:border-muted-foreground/30"
                  }`}
                >
                  <div
                    className={`flex h-10 w-10 items-center justify-center rounded-full ${
                      modelKey === "consensus"
                        ? "bg-primary text-primary-foreground"
                        : "bg-muted"
                    }`}
                  >
                    <GitBranch className="h-5 w-5" />
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-medium">Consenso</p>
                    <p className="text-xs text-muted-foreground">
                      Combina resultados de múltiples modelos
                    </p>
                  </div>
                  {modelKey === "consensus" && (
                    <Badge variant="success">Seleccionado</Badge>
                  )}
                </button>
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
              {result.consensus && <ConsensusView consensus={result.consensus} />}

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
                <Button variant="outline" className="flex-1" onClick={handleDownload}>
                  <Download className="mr-2 h-4 w-4" />
                  Descargar Reporte
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
