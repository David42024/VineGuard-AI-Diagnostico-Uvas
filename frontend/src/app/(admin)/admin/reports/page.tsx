"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { ErrorState } from "@/components/feedback/error-state";
import { EmptyState } from "@/components/feedback/empty-state";
import { FileText, Download, Search, RefreshCw } from "lucide-react";
import { formatDate } from "@/lib/utils";
import { toast } from "sonner";
import api, { ReportItem, DiagnosisListItem } from "@/lib/api";

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default function ReportsPage() {
  const [reports, setReports] = useState<ReportItem[]>([]);
  const [diagnoses, setDiagnoses] = useState<DiagnosisListItem[]>([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedDiagnosisId, setSelectedDiagnosisId] = useState<string>("");
  const [generating, setGenerating] = useState(false);

  const loadReports = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.get<{ reports: ReportItem[] }>("/reports");
      setReports(res.data.reports);
    } catch (err) {
      setError(
        "No se pudieron cargar los reportes. Verifica que el backend esté corriendo."
      );
    } finally {
      setLoading(false);
    }
  };

  const loadDiagnoses = async () => {
    try {
      const res = await api.get<{ items: DiagnosisListItem[] }>("/diagnoses", {
        params: { limit: 50 },
      });
      setDiagnoses(res.data.items);
    } catch {
      // Silencioso: el selector de generación es secundario a la lista de reportes
    }
  };

  useEffect(() => {
    loadReports();
    loadDiagnoses();
  }, []);

  const handleGenerate = async () => {
    if (!selectedDiagnosisId) {
      toast.error("Selecciona un diagnóstico primero");
      return;
    }
    setGenerating(true);
    try {
      await api.post(`/reports/diagnosis/${selectedDiagnosisId}`);
      toast.success("Reporte generado exitosamente");
      setSelectedDiagnosisId("");
      loadReports();
    } catch (err) {
      toast.error("No se pudo generar el reporte");
    } finally {
      setGenerating(false);
    }
  };

  const handleDownload = (report: ReportItem) => {
    const baseURL = api.defaults.baseURL;
    window.open(`${baseURL}/reports/${report.id}/download`, "_blank");
  };

  const filtered = reports.filter((r) =>
    r.filename.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Reportes</h2>
        <p className="text-muted-foreground">
          Visualiza y descarga reportes generados automáticamente
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Generar nuevo reporte</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-4 sm:flex-row sm:items-end">
          <div className="flex-1 space-y-2">
            <label className="text-sm font-medium">Diagnóstico</label>
            <Select
              value={selectedDiagnosisId}
              onValueChange={setSelectedDiagnosisId}
            >
              <SelectTrigger>
                <SelectValue placeholder="Selecciona un diagnóstico..." />
              </SelectTrigger>
              <SelectContent>
                {diagnoses.map((d) => (
                  <SelectItem key={d.id} value={String(d.id)}>
                    #{d.id} — {d.result} ({d.filename ?? "sin nombre"})
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <Button onClick={handleGenerate} disabled={generating}>
            {generating ? "Generando..." : "Generar reporte"}
          </Button>
        </CardContent>
      </Card>

      <div className="flex gap-4">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Buscar reportes..."
            className="pl-10"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <Button variant="outline" size="icon" onClick={loadReports}>
          <RefreshCw className="h-4 w-4" />
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Reportes Disponibles</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="space-y-3">
              {Array.from({ length: 4 }).map((_, i) => (
                <Skeleton key={i} className="h-10 w-full" />
              ))}
            </div>
          ) : error ? (
            <ErrorState message={error} onRetry={loadReports} />
          ) : filtered.length === 0 ? (
            <EmptyState
              title="Sin reportes"
              description="Todavía no se ha generado ningún reporte. Genera uno desde un diagnóstico existente arriba."
            />
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Archivo</TableHead>
                  <TableHead>Tamaño</TableHead>
                  <TableHead>Fecha</TableHead>
                  <TableHead>Acciones</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filtered.map((report) => (
                  <TableRow key={report.id}>
                    <TableCell className="font-medium">
                      <div className="flex items-center gap-2">
                        <FileText className="h-4 w-4 text-muted-foreground" />
                        {report.filename}
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline" className="uppercase">
                        {formatBytes(report.size_bytes)}
                      </Badge>
                    </TableCell>
                    <TableCell>{formatDate(report.created_at)}</TableCell>
                    <TableCell>
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => handleDownload(report)}
                      >
                        <Download className="h-4 w-4" />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}