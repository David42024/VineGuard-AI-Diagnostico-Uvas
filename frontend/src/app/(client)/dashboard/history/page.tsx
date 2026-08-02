"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter,
} from "@/components/ui/dialog";
import {
  Search,
  Eye,
  Trash2,
  Download,
  RotateCcw,
  ChevronLeft,
  ChevronRight,
  Leaf,
  X,
  AlertTriangle,
} from "lucide-react";
import { formatDate, formatConfidence } from "@/lib/formatters";
import { toast } from "sonner";
import { EmptyState } from "@/components/feedback/empty-state";
import { ErrorState } from "@/components/feedback/error-state";
import api, { getApiOrigin } from "@/lib/api";
import type { DiagnosisResponse } from "@/types";
import { useTranslation } from "@/i18n";

interface HistoryItem {
  id: number;
  filename: string;
  date: string;
  model: string;
  prediction: string;
  confidence: number;
  health_status: "healthy" | "diseased";
}

const ITEMS_PER_PAGE = 6;

export default function HistoryPage() {
  const t = useTranslation();
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [items, setItems] = useState<HistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [deleteConfirm, setDeleteConfirm] = useState<number | null>(null);
  const [viewItemId, setViewItemId] = useState<number | null>(null);
  const [detailData, setDetailData] = useState<DiagnosisResponse | null>(null);
  const [loadingDetail, setLoadingDetail] = useState(false);

  useEffect(() => {
    if (viewItemId === null) {
      setDetailData(null);
      return;
    }
    setLoadingDetail(true);
    setDetailData(null);
    api.get(`/diagnoses/${viewItemId}`)
      .then((res) => setDetailData(res.data))
      .catch(() => toast.error(t("history.toastDetailError")))
      .finally(() => setLoadingDetail(false));
  }, [viewItemId]);

  useEffect(() => {
    setLoading(true);
    api.get("/diagnoses?limit=100").then((res) => {
      const list = (res.data?.items || []).map((d: {
        id: number;
        filename?: string;
        created_at?: string;
        model_used?: string;
        result: string;
        confidence?: number;
      }) => ({
        id: d.id,
        filename: d.filename || t("dashboard.unknown"),
        date: d.created_at || "",
        model: d.model_used || "—",
        prediction: d.result?.replace(/_/g, " ") || "—",
        confidence: d.confidence ?? 0,
        health_status: d.result === "Healthy" ? "healthy" as const : "diseased" as const,
      }));
      setItems(list);
    }).catch(() => {
      setError(t("history.loadError"));
    }).finally(() => setLoading(false));
  }, []);

  const filtered = items.filter((h) =>
    h.filename.toLowerCase().includes(search.toLowerCase())
  );
  const totalPages = Math.ceil(filtered.length / ITEMS_PER_PAGE);
  const paged = filtered.slice(
    (page - 1) * ITEMS_PER_PAGE,
    page * ITEMS_PER_PAGE
  );

  const handleDelete = async (id: number) => {
    try {
      await api.delete(`/diagnoses/${id}`);
      setItems((prev) => prev.filter((item) => item.id !== id));
      toast.success(t("history.deleteSuccess").replace("{id}", String(id)));
    } catch {
      toast.error(t("history.deleteError"));
    }
    setDeleteConfirm(null);
  };

  const handleRepeat = async (item: HistoryItem) => {
    try {
      const formData = new FormData();
      formData.append("model_key", "consensus");
      await api.post(`/diagnoses/${item.id}/repeat`, formData);
      toast.success(t("history.repeatSuccess").replace("{filename}", item.filename));
    } catch {
      toast.error(t("history.repeatError"));
    }
  };

  const handleDownload = async (item: HistoryItem) => {
    try {
      const genRes = await api.post<{ download_url: string; filename: string }>(
        `/reports/diagnosis/${item.id}`,
        {}
      );
      const origin = getApiOrigin();
      const fileRes = await api.get(genRes.data.download_url, {
        baseURL: origin,
        responseType: "blob",
      });
      const blob = new Blob([fileRes.data]);
      const blobUrl = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = blobUrl;
      link.download = genRes.data.filename || `reporte_${item.id}.docx`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(blobUrl);
      toast.success(t("history.downloadSuccess").replace("{filename}", item.filename));
    } catch {
      toast.error(t("history.downloadError"));
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">
          {t("history.title")}
        </h2>
        <p className="text-muted-foreground">
          {t("history.subtitle")}
        </p>
      </div>

      <div className="flex gap-4">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder={t("history.searchPlaceholder")}
            className="pl-10"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
      </div>

      {paged.length === 0 ? (
        <EmptyState
          title={t("history.emptyTitle")}
          description={t("history.emptyDesc")}
          actionLabel={t("history.emptyAction")}
        />
      ) : (
        <>
          {/* Mobile: card view */}
          <div className="grid gap-4 md:hidden">
            {paged.map((item) => (
              <Card key={item.id}>
                <CardContent className="p-4 space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Leaf className="h-4 w-4 text-muted-foreground" />
                      <span className="text-sm font-medium">
                        {item.filename}
                      </span>
                    </div>
                    <Badge
                      variant={
                        item.health_status === "healthy"
                          ? "success"
                          : "destructive"
                      }
                    >
                      {item.prediction}
                    </Badge>
                  </div>
                  <div className="flex justify-between text-xs text-muted-foreground">
                    <span>{formatDate(item.date)}</span>
                    <span>{formatConfidence(item.confidence)}</span>
                  </div>
                  <div className="flex gap-2">
                    <Button variant="outline" size="sm" className="flex-1" onClick={() => setViewItemId(item.id)}>
                      <Eye className="h-4 w-4 mr-1" /> {t("history.view")}
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      className="flex-1"
                      onClick={() => handleRepeat(item)}
                    >
                      <RotateCcw className="h-4 w-4 mr-1" /> {t("history.repeat")}
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleDownload(item)}
                    >
                      <Download className="h-4 w-4" />
                    </Button>
                    <Dialog
                      open={deleteConfirm === item.id}
                      onOpenChange={(open) =>
                        setDeleteConfirm(open ? item.id : null)
                      }
                    >
                      <DialogTrigger asChild>
                        <Button
                          variant="outline"
                          size="sm"
                          className="text-destructive"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </DialogTrigger>
                      <DialogContent>
                        <DialogHeader>
                          <DialogTitle>{t("history.deleteDialogTitle")}</DialogTitle>
                          <DialogDescription>
                            {t("history.deleteDialogDesc").replace(
                              "{filename}",
                              item.filename
                            )}
                          </DialogDescription>
                        </DialogHeader>
                        <DialogFooter>
                          <Button
                            variant="outline"
                            onClick={() => setDeleteConfirm(null)}
                          >
                            {t("common.cancel")}
                          </Button>
                          <Button
                            variant="destructive"
                            onClick={() => handleDelete(item.id)}
                          >
                            {t("common.delete")}
                          </Button>
                        </DialogFooter>
                      </DialogContent>
                    </Dialog>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Desktop: table view */}
          <Card className="hidden md:block">
            <CardHeader>
              <CardTitle className="text-lg">{t("history.tableTitle")}</CardTitle>
            </CardHeader>
            <CardContent>
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b">
                    <th className="text-left font-medium text-muted-foreground p-3">{t("reports.columnFile")}</th>
                    <th className="text-left font-medium text-muted-foreground p-3">{t("reports.columnDate")}</th>
                    <th className="text-left font-medium text-muted-foreground p-3">{t("common.model")}</th>
                    <th className="text-left font-medium text-muted-foreground p-3">{t("admin.prediction")}</th>
                    <th className="text-left font-medium text-muted-foreground p-3">{t("result.confidence")}</th>
                    <th className="text-right font-medium text-muted-foreground p-3">{t("reports.columnActions")}</th>
                  </tr>
                </thead>
                <tbody>
                  {paged.map((item) => (
                    <tr key={item.id} className="border-b last:border-0">
                      <td className="p-3 font-medium">{item.filename}</td>
                      <td className="p-3 text-muted-foreground">
                        {formatDate(item.date)}
                      </td>
                      <td className="p-3">
                        <Badge variant="outline">{item.model}</Badge>
                      </td>
                      <td className="p-3">
                        <Badge
                          variant={
                            item.health_status === "healthy"
                              ? "success"
                              : "destructive"
                          }
                        >
                          {item.prediction}
                        </Badge>
                      </td>
                      <td className="p-3">
                        {formatConfidence(item.confidence)}
                      </td>
                      <td className="p-3 text-right">
                        <div className="flex justify-end gap-1">
                          <Button variant="ghost" size="icon" onClick={() => setViewItemId(item.id)}>
                            <Eye className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => handleRepeat(item)}
                          >
                            <RotateCcw className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => handleDownload(item)}
                          >
                            <Download className="h-4 w-4" />
                          </Button>
                          <Dialog
                            open={deleteConfirm === item.id}
                            onOpenChange={(open) =>
                              setDeleteConfirm(open ? item.id : null)
                            }
                          >
                            <DialogTrigger asChild>
                              <Button
                                variant="ghost"
                                size="icon"
                                className="text-destructive"
                              >
                                <Trash2 className="h-4 w-4" />
                              </Button>
                            </DialogTrigger>
                            <DialogContent>
                              <DialogHeader>
                                <DialogTitle>{t("history.deleteDialogTitle")}</DialogTitle>
                                <DialogDescription>
                                  {t("history.deleteDialogDesc").replace(
                                    "{filename}",
                                    item.filename
                                  )}
                                </DialogDescription>
                              </DialogHeader>
                              <DialogFooter>
                                <Button
                                  variant="outline"
                                  onClick={() => setDeleteConfirm(null)}
                                >
                                  {t("common.cancel")}
                                </Button>
                                <Button
                                  variant="destructive"
                                  onClick={() => handleDelete(item.id)}
                                >
                                  {t("common.delete")}
                                </Button>
                              </DialogFooter>
                            </DialogContent>
                          </Dialog>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </CardContent>
          </Card>

          <div className="flex items-center justify-between">
            <p className="text-sm text-muted-foreground">
              {t("history.pagination")
                .replace("{from}", String((page - 1) * ITEMS_PER_PAGE + 1))
                .replace("{to}", String(Math.min(page * ITEMS_PER_PAGE, filtered.length)))
                .replace("{total}", String(filtered.length))}
            </p>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPage(Math.max(1, page - 1))}
                disabled={page === 1}
              >
                <ChevronLeft className="h-4 w-4" />
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPage(Math.min(totalPages, page + 1))}
                disabled={page === totalPages}
              >
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </>
      )}

      {/* Detail view dialog */}
      <Dialog open={viewItemId !== null} onOpenChange={(open) => { if (!open) setViewItemId(null); }}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{t("history.detailTitle")}</DialogTitle>
            <DialogDescription>
              {t("history.detailDesc")}
            </DialogDescription>
          </DialogHeader>

          {loadingDetail && (
            <div className="flex justify-center py-8">
              <Skeleton className="h-64 w-full" />
            </div>
          )}

          {!loadingDetail && !detailData && (
            <p className="text-center text-muted-foreground py-8">
              {t("history.detailLoadError")}
            </p>
          )}

          {!loadingDetail && detailData && (
            <div className="space-y-6">
              {/* Image */}
              {detailData.image_url && (
                <div className="rounded-lg overflow-hidden border bg-muted/30">
                  <img
                    src={detailData.image_url}
                    alt={t("history.imageAlt")}
                    className="w-full max-h-80 object-contain"
                  />
                </div>
              )}

              {/* Prediction summary */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="rounded-lg border p-4 space-y-2">
                  <h4 className="text-sm font-medium text-muted-foreground">{t("admin.prediction")}</h4>
                  <p className="text-xl font-bold">{detailData.prediction.display_name}</p>
                  {detailData.prediction.health_status && (
                    <Badge variant={detailData.prediction.health_status === "healthy" ? "success" : "destructive"}>
                      {detailData.prediction.health_status === "healthy" ? t("disease.healthy") : t("disease.diseased")}
                    </Badge>
                  )}
                  {detailData.prediction.risk_level && detailData.prediction.risk_level !== "none" && (
                    <p className="text-xs text-muted-foreground">
                      {t("history.risk").replace("{risk}", detailData.prediction.risk_level)}
                    </p>
                  )}
                </div>
                <div className="rounded-lg border p-4 space-y-2">
                  <h4 className="text-sm font-medium text-muted-foreground">{t("result.confidence")}</h4>
                  <p className="text-2xl font-bold">{formatConfidence(detailData.prediction.confidence)}</p>
                  <div className="w-full bg-muted rounded-full h-2.5">
                    <div
                      className="bg-primary h-2.5 rounded-full transition-all"
                      style={{ width: `${Math.round(detailData.prediction.confidence * 100)}%` }}
                    />
                  </div>
                </div>
              </div>

              {/* Model & metadata */}
              <div className="rounded-lg border p-4 space-y-3">
                <h4 className="text-sm font-medium text-muted-foreground">{t("history.modelInfo")}</h4>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <span className="text-muted-foreground">{t("history.modelLabel")}</span>
                  <span>{detailData.model.name} ({detailData.model.key})</span>
                  <span className="text-muted-foreground">{t("history.versionLabel")}</span>
                  <span>{detailData.model.version}</span>
                  {detailData.created_at && (
                    <>
                      <span className="text-muted-foreground">{t("history.dateLabel")}</span>
                      <span>{formatDate(detailData.created_at)}</span>
                    </>
                  )}
                  {detailData.inference_time_ms != null && (
                    <>
                      <span className="text-muted-foreground">{t("history.inferenceTimeLabel")}</span>
                      <span>{detailData.inference_time_ms.toFixed(1)} ms</span>
                    </>
                  )}
                </div>
              </div>

              {/* Probabilities */}
              {detailData.probabilities && Object.keys(detailData.probabilities).length > 0 && (
                <div className="rounded-lg border p-4 space-y-3">
                  <h4 className="text-sm font-medium text-muted-foreground">{t("history.probabilitiesTitle")}</h4>
                  <div className="space-y-2">
                    {Object.entries(detailData.probabilities)
                      .sort(([, a], [, b]) => b - a)
                      .map(([cls, prob]) => (
                        <div key={cls} className="flex items-center gap-2 text-sm">
                          <span className="w-32 truncate font-medium">{cls.replace(/_/g, " ")}</span>
                          <div className="flex-1 bg-muted rounded-full h-2">
                            <div
                              className="bg-primary h-2 rounded-full transition-all"
                              style={{ width: `${Math.round(prob * 100)}%` }}
                            />
                          </div>
                          <span className="w-16 text-right text-muted-foreground">
                            {(prob * 100).toFixed(1)}%
                          </span>
                        </div>
                      ))}
                  </div>
                </div>
              )}

              {/* Warnings */}
              {detailData.warnings && detailData.warnings.length > 0 && (
                <div className="rounded-lg border border-yellow-300 bg-yellow-50 dark:bg-yellow-950/20 p-4 space-y-1">
                  {detailData.warnings.map((w, i) => (
                    <div key={i} className="flex items-center gap-2 text-sm text-yellow-800 dark:text-yellow-200">
                      <AlertTriangle className="h-4 w-4 shrink-0" />
                      <span>{w}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          <DialogFooter>
            <Button variant="outline" onClick={() => setViewItemId(null)}>
              {t("history.close")}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
