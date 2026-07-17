"use client";

import { CheckCircle2, XCircle, Clock, AlertCircle } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { cn, formatConfidence } from "@/lib/utils";
import type { PredictionDetail } from "@/types/api";

interface ComparisonViewProps {
  predictions: PredictionDetail[];
}

export function ComparisonView({ predictions }: ComparisonViewProps) {
  if (!predictions || predictions.length === 0) {
    return null;
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-lg">
          Comparación de Modelos
          <Badge variant="secondary">{predictions.length} modelos</Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {predictions.map((pred) => {
          const success = pred.status === "success";
          return (
            <div
              key={pred.model_key}
              className={cn(
                "rounded-lg border p-4 transition-colors",
                success
                  ? "border-border"
                  : "border-destructive/50 bg-destructive/5"
              )}
            >
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  {success ? (
                    <CheckCircle2 className="h-4 w-4 text-green-600" />
                  ) : (
                    <XCircle className="h-4 w-4 text-destructive" />
                  )}
                  <span className="font-medium text-sm">
                    {pred.model_name || pred.model_key}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  {success && pred.confidence != null && (
                    <Badge
                      variant={pred.confidence >= 0.8 ? "success" : pred.confidence >= 0.5 ? "warning" : "secondary"}
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

              {success ? (
                <>
                  <p className="text-sm mb-2">
                    <span className="text-muted-foreground">Predicción: </span>
                    <span className="font-semibold">
                      {pred.predicted_class?.replace(/_/g, " ") || "N/A"}
                    </span>
                  </p>
                  {pred.confidence != null && (
                    <div className="space-y-1">
                      <div className="flex justify-between text-xs text-muted-foreground">
                        <span>Confianza</span>
                        <span>{formatConfidence(pred.confidence)}</span>
                      </div>
                      <Progress value={pred.confidence * 100} className="h-1.5" />
                    </div>
                  )}
                  {pred.probabilities && pred.probabilities.length > 0 && (
                    <div className="mt-2 space-y-1">
                      {["Black_rot", "Esca", "Healthy", "Leaf_blight"].map((cls, idx) => (
                        <div key={cls} className="flex justify-between text-xs">
                          <span>{cls.replace(/_/g, " ")}</span>
                          <span>{formatConfidence(pred.probabilities![idx] ?? 0)}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </>
              ) : (
                <div className="flex items-start gap-2 text-sm text-destructive">
                  <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
                  <span>{pred.error || "Error en la predicción"}</span>
                </div>
              )}
            </div>
          );
        })}
      </CardContent>
    </Card>
  );
}
