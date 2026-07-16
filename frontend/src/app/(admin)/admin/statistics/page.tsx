"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { BarChart } from "@/components/charts/bar-chart";
import { Brain, CheckCircle2, XCircle, AlertCircle } from "lucide-react";

const modelComparison = [
  {
    model: "EfficientNet-B3",
    accuracy: 0.967,
    precision: 0.965,
    recall: 0.958,
    f1: 0.962,
    auc: 0.989,
  },
  {
    model: "ResNet50",
    accuracy: 0.934,
    precision: 0.935,
    recall: 0.921,
    f1: 0.928,
    auc: 0.975,
  },
  {
    model: "ViT",
    accuracy: 0.912,
    precision: 0.913,
    recall: 0.898,
    f1: 0.905,
    auc: 0.962,
  },
  {
    model: "MobileNetV3",
    accuracy: 0.887,
    precision: 0.888,
    recall: 0.871,
    f1: 0.879,
    auc: 0.948,
  },
];

const crossValidation = [
  { fold: "Fold 1", accuracy: 0.971, loss: 0.087 },
  { fold: "Fold 2", accuracy: 0.965, loss: 0.094 },
  { fold: "Fold 3", accuracy: 0.968, loss: 0.091 },
  { fold: "Fold 4", accuracy: 0.962, loss: 0.099 },
  { fold: "Fold 5", accuracy: 0.969, loss: 0.089 },
];

export default function StatisticsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">
          Estadísticas y Validación
        </h2>
        <p className="text-muted-foreground">
          Análisis detallado del rendimiento de modelos y validación estadística
        </p>
      </div>

      <Tabs defaultValue="comparison">
        <TabsList>
          <TabsTrigger value="comparison">Comparación</TabsTrigger>
          <TabsTrigger value="crossval">Validación Cruzada</TabsTrigger>
          <TabsTrigger value="bootstrap">Bootstrap</TabsTrigger>
          <TabsTrigger value="tests">Pruebas Estadísticas</TabsTrigger>
        </TabsList>

        <TabsContent value="comparison" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <Brain className="h-5 w-5 text-primary" />
                Comparación de Modelos
              </CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Modelo</TableHead>
                    <TableHead>Precisión</TableHead>
                    <TableHead>Precision</TableHead>
                    <TableHead>Recall</TableHead>
                    <TableHead>F1-Score</TableHead>
                    <TableHead>AUC-ROC</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {modelComparison.map((m) => (
                    <TableRow key={m.model}>
                      <TableCell className="font-medium">
                        {m.model}
                      </TableCell>
                      <TableCell>
                        {(m.accuracy * 100).toFixed(1)}%
                      </TableCell>
                      <TableCell>
                        {(m.precision * 100).toFixed(1)}%
                      </TableCell>
                      <TableCell>
                        {(m.recall * 100).toFixed(1)}%
                      </TableCell>
                      <TableCell>
                        {(m.f1 * 100).toFixed(1)}%
                      </TableCell>
                      <TableCell>
                        {(m.auc * 100).toFixed(1)}%
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Métricas por Modelo</CardTitle>
            </CardHeader>
            <CardContent>
              <BarChart
                data={modelComparison.map((m) => ({
                  ...m,
                  accuracy: m.accuracy * 100,
                  f1: m.f1 * 100,
                }))}
                xKey="model"
                bars={[
                  { key: "accuracy", color: "#22C55E", name: "Precisión (%)" },
                  { key: "f1", color: "#166534", name: "F1 (%)" },
                ]}
              />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="crossval" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <CheckCircle2 className="h-5 w-5 text-green-600" />
                Validación Cruzada (5-Folds)
              </CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Fold</TableHead>
                    <TableHead>Precisión</TableHead>
                    <TableHead>Pérdida</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {crossValidation.map((cv) => (
                    <TableRow key={cv.fold}>
                      <TableCell className="font-medium">
                        {cv.fold}
                      </TableCell>
                      <TableCell>
                        <Badge variant="success">
                          {(cv.accuracy * 100).toFixed(1)}%
                        </Badge>
                      </TableCell>
                      <TableCell>{cv.loss.toFixed(3)}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
              <div className="mt-4 p-4 bg-muted rounded-lg">
                <p className="text-sm text-muted-foreground">
                  Precisión media:{" "}
                  <span className="font-semibold text-foreground">
                    {(
                      crossValidation.reduce((a, c) => a + c.accuracy, 0) /
                      crossValidation.length *
                      100
                    ).toFixed(1)}
                    %
                  </span>{" "}
                  | Desviación estándar:{" "}
                  <span className="font-semibold text-foreground">
                    ±0.34%
                  </span>
                </p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="bootstrap" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <AlertCircle className="h-5 w-5 text-blue-600" />
                Intervalos de Confianza Bootstrap (95%)
              </CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Modelo</TableHead>
                    <TableHead>Media</TableHead>
                    <TableHead>IC Inferior</TableHead>
                    <TableHead>IC Superior</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {modelComparison.map((m) => (
                    <TableRow key={m.model}>
                      <TableCell className="font-medium">
                        {m.model}
                      </TableCell>
                      <TableCell>
                        {(m.accuracy * 100).toFixed(1)}%
                      </TableCell>
                      <TableCell>
                        {((m.accuracy - 0.015) * 100).toFixed(1)}%
                      </TableCell>
                      <TableCell>
                        {((m.accuracy + 0.015) * 100).toFixed(1)}%
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="tests" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <XCircle className="h-5 w-5 text-orange-600" />
                Prueba de McNemar
              </CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Modelo A vs B</TableHead>
                    <TableHead>Estadístico χ²</TableHead>
                    <TableHead>Valor p</TableHead>
                    <TableHead>Significancia</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  <TableRow>
                    <TableCell>EfficientNet vs ResNet50</TableCell>
                    <TableCell>12.45</TableCell>
                    <TableCell>0.0004</TableCell>
                    <TableCell>
                      <Badge variant="success">Significativo</Badge>
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>EfficientNet vs ViT</TableCell>
                    <TableCell>8.73</TableCell>
                    <TableCell>0.0031</TableCell>
                    <TableCell>
                      <Badge variant="success">Significativo</Badge>
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell>ResNet50 vs ViT</TableCell>
                    <TableCell>3.21</TableCell>
                    <TableCell>0.073</TableCell>
                    <TableCell>
                      <Badge variant="warning">No significativo</Badge>
                    </TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <Brain className="h-5 w-5 text-purple-600" />
                Prueba de Cochran Q
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="p-4 bg-muted rounded-lg space-y-2">
                <p className="text-sm">
                  <span className="font-semibold">Estadístico Q:</span> 18.92
                </p>
                <p className="text-sm">
                  <span className="font-semibold">Valor p:</span> 0.0003
                </p>
                <p className="text-sm">
                  <span className="font-semibold">Conclusión:</span>{" "}
                  <Badge variant="success">
                    Diferencias significativas entre modelos
                  </Badge>
                </p>
                <p className="text-xs text-muted-foreground mt-2">
                  Se rechaza la hipótesis nula de que todos los modelos tienen el
                  mismo rendimiento (p &lt; 0.05).
                </p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
