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
import { useTranslation } from "@/i18n";

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default function ReportsPage() {
  const t = useTranslation();
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
      setError(t("reports.error"));
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
      toast.error(t("reports.toastSelectDiagnosis"));
      return;
    }
    setGenerating(true);
    try {
      await api.post(`/reports/diagnosis/${selectedDiagnosisId}`);
      toast.success(t("reports.toastSuccess"));
      setSelectedDiagnosisId("");
      loadReports();
    } catch (err) {
      toast.error(t("reports.toastError"));
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
        <h2 className="text-3xl font-bold tracking-tight">{t("reports.title")}</h2>
        <p className="text-muted-foreground">
          {t("reports.subtitle")}
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">{t("reports.generateNew")}</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-4 sm:flex-row sm:items-end">
          <div className="flex-1 space-y-2">
            <label className="text-sm font-medium">{t("reports.diagnosisLabel")}</label>
            <Select
              value={selectedDiagnosisId}
              onValueChange={setSelectedDiagnosisId}
            >
              <SelectTrigger>
                <SelectValue placeholder={t("reports.selectDiagnosis")} />
              </SelectTrigger>
              <SelectContent>
                {diagnoses.map((d) => (
                  <SelectItem key={d.id} value={String(d.id)}>
                    #{d.id} — {d.result} ({d.filename ?? t("reports.noFilename")})
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <Button onClick={handleGenerate} disabled={generating}>
            {generating ? t("reports.generating") : t("reports.generateBtn")}
          </Button>
        </CardContent>
      </Card>

      <div className="flex gap-4">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder={t("reports.searchPlaceholder")}
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
          <CardTitle className="text-lg">{t("reports.available")}</CardTitle>
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
              title={t("reports.noReportsTitle")}
              description={t("reports.noReportsDesc")}
            />
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>{t("reports.columnFile")}</TableHead>
                  <TableHead>{t("reports.columnSize")}</TableHead>
                  <TableHead>{t("reports.columnDate")}</TableHead>
                  <TableHead>{t("reports.columnActions")}</TableHead>
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