"use client";

import { CheckCircle2, XCircle, Clock, AlertCircle, Trophy } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
import { cn, formatConfidence } from "@/lib/utils";
import type { PredictionDetail, ModelRanking } from "@/types/api";
import { formatClassName, MODEL_NAMES } from "@/lib/constants";
import { useTranslation } from "@/i18n";

interface ComparisonViewProps {
  predictions: PredictionDetail[];
  consensusClass?: string;
  ranking?: ModelRanking[];
}

export function ComparisonView({ predictions, consensusClass, ranking }: ComparisonViewProps) {
  const t = useTranslation();
  if (!predictions || predictions.length === 0) return null;

  const successful = predictions.filter((p) => p.status === "success");

  const majorityClass =
    consensusClass ||
    (() => {
      const classes = successful.map((p) => p.predicted_class);
      return classes.length
        ? classes.sort((a, b) =>
            classes.filter((c) => c === b).length -
            classes.filter((c) => c === a).length
          )[0]
        : "";
    })();

  const agreeingCount = successful.filter(
    (p) => p.predicted_class === majorityClass
  ).length;

  const confidences = successful
    .map((p) => p.confidence ?? 0)
    .filter((c) => c > 0);
  const maxConf = confidences.length ? Math.max(...confidences) : 0;
  const minConf = confidences.length ? Math.min(...confidences) : 0;
  const maxDiff = maxConf - minConf;

  // Build ranking lookup by model_key
  const rankingMap: Record<string, number> = {};
  if (ranking) {
    ranking.forEach((r) => {
      const key =
        Object.entries(MODEL_NAMES).find(
          ([, v]) => v === r.modelo || r.modelo.includes(v)
        )?.[0] || "";
      if (key) rankingMap[key] = r.ranking;
    });
  }

  // Sort predictions: by ranking first, then by model_key
  const sorted = [...predictions].sort((a, b) => {
    if (ranking && ranking.length > 0) {
      const ra = rankingMap[a.model_key] ?? 99;
      const rb = rankingMap[b.model_key] ?? 99;
      if (ra !== rb) return ra - rb;
    }
    return a.model_key.localeCompare(b.model_key);
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-lg">
          {t("comparison.title")}
          <Badge variant="secondary">{t("comparison.modelsCount").replace("{count}", String(predictions.length))}</Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Summary header */}
        <div className="rounded-lg border bg-muted/30 p-4 space-y-3">
          <div className="flex items-center gap-2">
            <Trophy className="h-5 w-5 text-yellow-500" />
            <span className="font-semibold">
              {t("comparison.overallResult")} {formatClassName(majorityClass)}
            </span>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-sm">
            <div>
              <p className="text-muted-foreground text-xs">{t("comparison.matchingModels")}</p>
              <p className="font-medium">
                {agreeingCount} de {successful.length}
              </p>
            </div>
            <div>
              <p className="text-muted-foreground text-xs">{t("comparison.highestConfidence")}</p>
              <p className="font-medium">{formatConfidence(maxConf)}</p>
            </div>
            <div>
              <p className="text-muted-foreground text-xs">{t("comparison.lowestConfidence")}</p>
              <p className="font-medium">{formatConfidence(minConf)}</p>
            </div>
            <div>
              <p className="text-muted-foreground text-xs">{t("comparison.maxDifference")}</p>
              <p className="font-medium">{formatConfidence(maxDiff)}</p>
            </div>
          </div>
        </div>

        {/* Individual model cards */}
        <div className="space-y-3">
          {sorted.map((pred, idx) => {
            const success = pred.status === "success";
            const agreesWithMajority =
              success && pred.predicted_class === majorityClass;
            const modelRank = rankingMap[pred.model_key];
            return (
              <div
                key={pred.model_key}
                className={cn(
                  "rounded-lg border p-4 transition-colors",
                  success
                    ? agreesWithMajority
                      ? "border-green-200 dark:border-green-800"
                      : "border-amber-200 dark:border-amber-800"
                    : "border-destructive/50 bg-destructive/5"
                )}
              >
                {/* Header row */}
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    {success ? (
                      agreesWithMajority ? (
                        <CheckCircle2 className="h-4 w-4 text-green-600" />
                      ) : (
                        <XCircle className="h-4 w-4 text-amber-600" />
                      )
                    ) : (
                      <XCircle className="h-4 w-4 text-destructive" />
                    )}
                    <span className="font-medium text-sm">
                      {MODEL_NAMES[pred.model_key] || pred.model_name || pred.model_key}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    {modelRank != null && (
                      <div className="flex items-center gap-1 text-xs text-muted-foreground">
                        {modelRank === 1 ? (
                          <Trophy className="h-3 w-3 text-yellow-500" />
                        ) : (
                          <span className="text-muted-foreground">#{modelRank}</span>
                        )}
                      </div>
                    )}
                    {success && pred.confidence != null && (
                      <Badge
                        variant={
                          pred.confidence >= 0.8
                            ? "success"
                            : pred.confidence >= 0.5
                              ? "warning"
                              : "secondary"
                        }
                      >
                        {formatConfidence(pred.confidence)}
                      </Badge>
                    )}
                    {pred.inference_time_ms != null && (
                      <span className="text-xs text-muted-foreground flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        {(pred.inference_time_ms / 1000).toFixed(2)}s
                      </span>
                    )}
                  </div>
                </div>

                {/* Prediction detail */}
                {success ? (
                  <>
                    <div className="flex items-center justify-between text-sm mb-2">
                      <span>
                        <span className="text-muted-foreground">{t("comparison.prediction")} </span>
                        <span className="font-semibold">
                          {formatClassName(pred.predicted_class)}
                        </span>
                      </span>
                      <span
                        className={cn(
                          "text-xs font-medium",
                          agreesWithMajority
                            ? "text-green-600"
                            : "text-amber-600"
                        )}
                      >
                        {agreesWithMajority
                          ? t("comparison.agreesWithMajority")
                          : t("comparison.differsFromMajority")}
                      </span>
                    </div>

                    {pred.confidence != null && (
                      <div className="space-y-1 mb-2">
                        <div className="flex justify-between text-xs text-muted-foreground">
                          <span>{t("comparison.confidence")}</span>
                          <span>{formatConfidence(pred.confidence)}</span>
                        </div>
                        <Progress value={pred.confidence * 100} className="h-1.5" />
                      </div>
                    )}

                    {pred.probabilities && pred.probabilities.length > 0 && (
                      <div className="mt-2 space-y-1">
                        <p className="text-xs text-muted-foreground mb-1">
                          {t("comparison.probabilityDistribution")}
                        </p>
                        {["Black_rot", "Esca", "Healthy", "Leaf_blight"].map(
                          (cls, idx) => (
                            <div key={cls} className="flex items-center gap-2 text-xs">
                              <span className="w-24 truncate">{formatClassName(cls)}</span>
                              <div className="flex-1 bg-muted rounded-full h-1.5">
                                <div
                                  className="bg-primary h-1.5 rounded-full"
                                  style={{
                                    width: `${(pred.probabilities![idx] ?? 0) * 100}%`,
                                  }}
                                />
                              </div>
                              <span className="w-14 text-right text-muted-foreground">
                                {formatConfidence(pred.probabilities![idx] ?? 0)}
                              </span>
                            </div>
                          )
                        )}
                      </div>
                    )}
                  </>
                ) : (
                  <div className="flex items-start gap-2 text-sm text-destructive">
                    <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
                    <span>{pred.error || t("comparison.error")}</span>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
