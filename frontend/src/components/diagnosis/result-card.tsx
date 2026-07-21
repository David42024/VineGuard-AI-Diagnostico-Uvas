"use client";

import { Leaf, Bug, Clock, FlaskConical } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
import { cn, formatConfidence, formatDate } from "@/lib/utils";
import type { DiagnosisResponse } from "@/types/api";
import { formatClassName, MODE_LABELS, MODEL_NAMES } from "@/lib/constants";
import { useTranslation } from "@/i18n";

interface ResultCardProps {
  diagnosis: DiagnosisResponse;
}

export function ResultCard({ diagnosis }: ResultCardProps) {
  const t = useTranslation();
  const {
    prediction,
    model,
    inference_time_ms,
    created_at,
    probabilities,
    mode,
    mode_label,
  } = diagnosis;

  const isHealthy = prediction.health_status === "healthy";
  const modeDisplay = mode_label || MODE_LABELS[mode] || model.name;

  return (
    <Card className="overflow-hidden">
      <div
        className={cn("h-2", isHealthy ? "bg-green-500" : "bg-red-500")}
      />
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            {isHealthy ? (
              <Leaf className="h-5 w-5 text-green-600" />
            ) : (
              <Bug className="h-5 w-5 text-red-600" />
            )}
            {prediction.display_name || formatClassName(prediction.class_code)}
          </CardTitle>
          <Badge variant={isHealthy ? "success" : "destructive"}>
            {isHealthy ? t("result.healthy") : t("result.diseased")}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="rounded-md bg-muted/50 p-3 space-y-1 text-sm">
          <div className="flex justify-between">
            <span className="text-muted-foreground">{t("result.diagnosisMethod")}</span>
            <span className="font-medium">{modeDisplay}</span>
          </div>
          {mode === "best_model" && (
            <div className="flex justify-between">
              <span className="text-muted-foreground">{t("result.modelUsed")}</span>
              <span className="font-medium">{model.name}</span>
            </div>
          )}
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-sm text-muted-foreground">{t("result.class")}</p>
            <p className="text-sm font-medium">
              {formatClassName(prediction.class_code)}
            </p>
          </div>
          <div>
            <p className="text-sm text-muted-foreground">{t("result.risk")}</p>
            <span
              className={cn(
                "text-sm font-semibold",
                prediction.risk_level === "high"
                  ? "text-red-600"
                  : prediction.risk_level === "moderate"
                    ? "text-yellow-600"
                    : "text-green-600"
              )}
            >
              {prediction.risk_level || "N/A"}
            </span>
          </div>
        </div>

        <Separator />

        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium">
              {mode === "consensus" ? t("result.consensusConfidence") : t("result.confidence")}
            </span>
            <span className="text-sm font-bold">
              {formatConfidence(prediction.confidence)}
            </span>
          </div>
          <Progress value={prediction.confidence * 100} />
        </div>

        {mode === "consensus" && diagnosis.consensus?.confidence_description && (
          <p className="text-xs text-muted-foreground italic">
            {diagnosis.consensus.confidence_description}
          </p>
        )}

        {probabilities && Object.keys(probabilities).length > 0 && (
          <>
            <Separator />
            <div className="space-y-3">
              <p className="text-sm font-medium">
                {t("result.probabilityDistribution")}
              </p>
              {Object.entries(probabilities).map(([cls, prob]) => (
                <div key={cls} className="space-y-1">
                  <div className="flex justify-between text-xs">
                    <span>{formatClassName(cls)}</span>
                    <span>{formatConfidence(prob)}</span>
                  </div>
                  <Progress value={prob * 100} className="h-2" />
                </div>
              ))}
            </div>
          </>
        )}

        <Separator />

        <div className="flex flex-wrap gap-4 text-sm text-muted-foreground">
          <div className="flex items-center gap-1">
            <div className="flex items-center gap-1">
              <Clock className="h-4 w-4" />
              {inference_time_ms != null
                ? `${(inference_time_ms / 1000).toFixed(2)}s`
                : "N/A"}
            </div>
          </div>
          <div className="flex items-center gap-1">
            <FlaskConical className="h-4 w-4" />
            {created_at ? formatDate(created_at) : "N/A"}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
