"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Brain, RefreshCw, Star } from "lucide-react";
import { ErrorState } from "@/components/feedback/error-state";

interface ModelData {
  id: number;
  name: string;
  type: string;
  status: string;
  metrics: Record<string, number>;
  isBest?: boolean;
}

const mockModels: ModelData[] = [
  {
    id: 1,
    name: "EfficientNet-B3",
    type: "CNN",
    status: "production",
    metrics: { accuracy: 0.967, f1: 0.962, recall: 0.958, precision: 0.965 },
    isBest: true,
  },
  {
    id: 2,
    name: "ResNet50",
    type: "CNN",
    status: "production",
    metrics: { accuracy: 0.934, f1: 0.928, recall: 0.921, precision: 0.935 },
  },
  {
    id: 3,
    name: "Vision Transformer",
    type: "Transformer",
    status: "production",
    metrics: { accuracy: 0.912, f1: 0.905, recall: 0.898, precision: 0.913 },
  },
  {
    id: 4,
    name: "MobileNetV3",
    type: "CNN",
    status: "staging",
    metrics: { accuracy: 0.887, f1: 0.879, recall: 0.871, precision: 0.888 },
  },
  {
    id: 5,
    name: "CNN Base",
    type: "CNN",
    status: "archived",
    metrics: { accuracy: 0.852, f1: 0.843, recall: 0.835, precision: 0.854 },
  },
];

export default function ModelsPage() {
  const [models] = useState<ModelData[]>(mockModels);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const fetchModels = async () => {
    setLoading(true);
    setError("");
    try {
      await new Promise((r) => setTimeout(r, 1000));
    } catch {
      setError("Error al cargar modelos");
    } finally {
      setLoading(false);
    }
  };

  if (error) return <ErrorState message={error} onRetry={fetchModels} />;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">
            Gestión de Modelos
          </h2>
          <p className="text-muted-foreground">
            Visualiza y gestiona los modelos de IA disponibles
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={fetchModels} disabled={loading}>
          <RefreshCw className={`mr-2 h-4 w-4 ${loading ? "animate-spin" : ""}`} />
          Cargar modelos
        </Button>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {models.map((model) => (
          <Card key={model.id} className="relative overflow-hidden">
            {model.isBest && (
              <div className="absolute right-2 top-2">
                <Badge variant="success" className="gap-1">
                  <Star className="h-3 w-3" />
                  Mejor
                </Badge>
              </div>
            )}
            <CardHeader>
              <div className="flex items-center gap-2">
                <Brain className="h-5 w-5 text-primary" />
                <CardTitle className="text-lg">{model.name}</CardTitle>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex gap-2">
                <Badge variant="secondary">{model.type}</Badge>
                <Badge
                  variant={
                    model.status === "production"
                      ? "success"
                      : model.status === "staging"
                      ? "warning"
                      : "secondary"
                  }
                >
                  {model.status === "production"
                    ? "Producción"
                    : model.status === "staging"
                    ? "Pruebas"
                    : "Archivado"}
                </Badge>
              </div>
              <div className="space-y-2">
                {Object.entries(model.metrics).map(([key, value]) => (
                  <div key={key} className="flex justify-between text-sm">
                    <span className="text-muted-foreground capitalize">
                      {key}
                    </span>
                    <span className="font-medium">
                      {(value * 100).toFixed(1)}%
                    </span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Ranking de Modelos</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>#</TableHead>
                <TableHead>Modelo</TableHead>
                <TableHead>Tipo</TableHead>
                <TableHead>Precisión</TableHead>
                <TableHead>F1-Score</TableHead>
                <TableHead>Recall</TableHead>
                <TableHead>Estado</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {[...models]
                .sort(
                  (a, b) => b.metrics.accuracy - a.metrics.accuracy
                )
                .map((model, index) => (
                  <TableRow key={model.id}>
                    <TableCell className="font-medium">
                      {index + 1}
                    </TableCell>
                    <TableCell>{model.name}</TableCell>
                    <TableCell>{model.type}</TableCell>
                    <TableCell>
                      {(model.metrics.accuracy * 100).toFixed(1)}%
                    </TableCell>
                    <TableCell>
                      {(model.metrics.f1 * 100).toFixed(1)}%
                    </TableCell>
                    <TableCell>
                      {(model.metrics.recall * 100).toFixed(1)}%
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant={
                          model.status === "production"
                            ? "success"
                            : model.status === "staging"
                            ? "warning"
                            : "secondary"
                        }
                      >
                        {model.status}
                      </Badge>
                    </TableCell>
                  </TableRow>
                ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
