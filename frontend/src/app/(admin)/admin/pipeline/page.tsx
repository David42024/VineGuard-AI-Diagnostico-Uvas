"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  CheckCircle2,
  Loader2,
  XCircle,
  Circle,
  ChevronDown,
  ChevronUp,
  RefreshCw,
  Database,
  Image as ImageIcon,
  Brain,
  BarChart3,
  FileText,
  FlaskConical,
} from "lucide-react";
import { cn } from "@/lib/utils";

interface PipelineStageData {
  label: string;
  status: "completed" | "pending" | "error" | "running";
  detail: string;
  icon: React.ElementType;
}

const defaultStages: PipelineStageData[] = [
  {
    label: "Carga de Dataset",
    status: "completed",
    detail: "Dataset original cargado correctamente (12,000 imágenes)",
    icon: Database,
  },
  {
    label: "Preprocesamiento",
    status: "completed",
    detail: "Imágenes redimensionadas a 224x224, normalización aplicada",
    icon: ImageIcon,
  },
  {
    label: "Aumento de Datos",
    status: "completed",
    detail: "Rotaciones, volteos y ajustes de brillo aplicados",
    icon: ImageIcon,
  },
  {
    label: "Entrenamiento de Modelos",
    status: "running",
    detail: "M1 - SVM en entrenamiento (época 42/100)",
    icon: Brain,
  },
  {
    label: "Validación Cruzada",
    status: "pending",
    detail: "Pendiente - 5 folds configurados",
    icon: BarChart3,
  },
  {
    label: "Evaluación",
    status: "pending",
    detail: "Pendiente - Esperando finalización de entrenamiento",
    icon: FlaskConical,
  },
  {
    label: "Generación de Reportes",
    status: "pending",
    detail: "Pendiente - Se generará automáticamente",
    icon: FileText,
  },
];

const statusIcon = {
  completed: CheckCircle2,
  running: Loader2,
  error: XCircle,
  pending: Circle,
};

const statusColor = {
  completed: "text-green-600",
  running: "text-blue-600",
  error: "text-red-600",
  pending: "text-muted-foreground",
};

const statusBg = {
  completed: "border-green-200 bg-green-50 dark:border-green-800 dark:bg-green-950",
  running: "border-blue-200 bg-blue-50 dark:border-blue-800 dark:bg-blue-950",
  error: "border-red-200 bg-red-50 dark:border-red-800 dark:bg-red-950",
  pending: "border-muted bg-card",
};

export default function PipelinePage() {
  const [stages] = useState(defaultStages);
  const [expanded, setExpanded] = useState<number | null>(null);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">
            Estado del Pipeline
          </h2>
          <p className="text-muted-foreground">
            Visualiza el progreso del pipeline de entrenamiento y evaluación
          </p>
        </div>
        <Button variant="outline" size="sm">
          <RefreshCw className="mr-2 h-4 w-4" />
          Actualizar
        </Button>
      </div>

      <div className="relative">
        <div className="absolute left-8 top-0 bottom-0 w-px bg-border" />
        <div className="space-y-6 relative">
          {stages.map((stage, index) => {
            const Icon = stage.icon;
            const StatusIcon = statusIcon[stage.status];
            const isExpanded = expanded === index;

            return (
              <div key={index} className="relative pl-16">
                <div
                  className={cn(
                    "absolute left-5 top-1 flex h-7 w-7 items-center justify-center rounded-full border-2 bg-background",
                    stage.status === "completed" && "border-green-500",
                    stage.status === "running" && "border-blue-500",
                    stage.status === "error" && "border-red-500",
                    stage.status === "pending" && "border-muted-foreground"
                  )}
                >
                  <StatusIcon
                    className={cn(
                      "h-4 w-4",
                      statusColor[stage.status],
                      stage.status === "running" && "animate-spin"
                    )}
                  />
                </div>

                <Card
                  className={cn(
                    "cursor-pointer transition-all",
                    statusBg[stage.status]
                  )}
                  onClick={() =>
                    setExpanded(isExpanded ? null : index)
                  }
                >
                  <CardHeader className="py-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <Icon className={cn("h-5 w-5", statusColor[stage.status])} />
                        <div>
                          <CardTitle className="text-base">
                            {stage.label}
                          </CardTitle>
                          <Badge
                            variant={
                              stage.status === "completed"
                                ? "success"
                                : stage.status === "running"
                                ? "default"
                                : stage.status === "error"
                                ? "destructive"
                                : "secondary"
                            }
                            className="mt-1"
                          >
                            {stage.status === "completed"
                              ? "Completado"
                              : stage.status === "running"
                              ? "En progreso"
                              : stage.status === "error"
                              ? "Error"
                              : "Pendiente"}
                          </Badge>
                        </div>
                      </div>
                      {isExpanded ? (
                        <ChevronUp className="h-4 w-4 text-muted-foreground" />
                      ) : (
                        <ChevronDown className="h-4 w-4 text-muted-foreground" />
                      )}
                    </div>
                  </CardHeader>
                  {isExpanded && (
                    <CardContent className="pb-4 pt-0">
                      <p className="text-sm text-muted-foreground">
                        {stage.detail}
                      </p>
                    </CardContent>
                  )}
                </Card>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
