"use client";

import { Leaf, Bug, Clock, Brain, FlaskConical } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
import { cn, formatConfidence, formatDate } from "@/lib/utils";
import type { Diagnosis } from "@/lib/api";

interface ResultCardProps {
  diagnosis: Diagnosis;
}

export function ResultCard({ diagnosis }: ResultCardProps) {
  const {
    prediction,
    model,
    inference_time_ms,
    created_at,
    probabilities,
  } = diagnosis;

  const isHealthy = prediction.health_status === "healthy";

  return (
    <Card className="overflow-hidden">
      <div
        className={cn(
          "h-2",
          isHealthy ? "bg-green-500" : "bg-red-500"
        )}
      />
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            {isHealthy ? (
              <Leaf className="h-5 w-5 text-green-600" />
            ) : (
              <Bug className="h-5 w-5 text-red-600" />
            )}
            {prediction.display_name}
          </CardTitle>
          <Badge variant={isHealthy ? "success" : "destructive"}>
            {isHealthy ? "Sana" : "Enfermedad detectada"}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-sm text-muted-foreground">Clase</p>
            <p className="text-sm font-medium">{prediction.class_code.replace(/_/g, " ")}</p>
          </div>
          <div>
            <p className="text-sm text-muted-foreground">Nivel de riesgo</p>
            <span className={cn("text-sm font-semibold",
              prediction.risk_level === "high" ? "text-red-600" :
              prediction.risk_level === "moderate" ? "text-yellow-600" :
              "text-green-600"
            )}>
              {prediction.risk_level || "N/A"}
            </span>
          </div>
        </div>

        <Separator />

        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium">Confianza</span>
            <span className="text-sm font-bold">
              {formatConfidence(prediction.confidence)}
            </span>
          </div>
          <Progress value={prediction.confidence * 100} />
        </div>

        <Separator />

        <div className="space-y-3">
          <p className="text-sm font-medium">Distribución de Probabilidades</p>
          {probabilities && Object.entries(probabilities).map(([cls, prob]) => (
            <div key={cls} className="space-y-1">
              <div className="flex justify-between text-xs">
                <span>{cls.replace(/_/g, " ")}</span>
                <span>{formatConfidence(prob)}</span>
              </div>
              <Progress value={prob * 100} className="h-2" />
            </div>
          ))}
        </div>

        <Separator />

        <div className="flex flex-wrap gap-4 text-sm text-muted-foreground">
          <div className="flex items-center gap-1">
            <Brain className="h-4 w-4" />
            {model.name}
          </div>
          <div className="flex items-center gap-1">
            <Clock className="h-4 w-4" />
            {inference_time_ms != null ? `${(inference_time_ms / 1000).toFixed(2)}s` : "N/A"}
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
