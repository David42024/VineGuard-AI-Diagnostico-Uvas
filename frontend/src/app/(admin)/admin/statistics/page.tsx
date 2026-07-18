"use client";

import { useEffect, useState } from "react";
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
import { ErrorState } from "@/components/feedback/error-state";
import {
  Brain,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Lightbulb,
  Loader2,
} from "lucide-react";
import api from "@/lib/api";

interface RankingRow {
  modelo: string;
  accuracy: number;
  f1_score: number;
  f1_macro?: number;
  mcc?: number;
  precision?: number;
  recall?: number;
  acc_ci_inf: number;
  acc_ci_sup: number;
}

interface CrossValFold {
  modelo?: string;
  fold: string;
  accuracy: number;
  f1_macro: number;
  mcc?: number;
}

interface CrossValSummary {
  modelo: string;
  accuracy_mean: number;
  accuracy_std: number;
  f1_mean: number;
  f1_std: number;
  mcc_mean: number;
  mcc_std: number;
}

interface BootstrapRow {
  modelo: string;
  metric: string;
  mean: number;
  ci_inf: number;
  ci_sup: number;
}

interface McNemarRow {
  comparacion: string;
  estadistico: number;
  p_valor: number;
  significancia: string;
}

interface CochranQ {
  q_statistic: number;
  p_value: number;
  significancia: string;
}

interface FlatModel {
  model: string;
  accuracy: number;
  precision: number;
  recall: number;
  f1: number;
  auc: number;
}

export default function StatisticsPage() {
  const [ranking, setRanking] = useState<RankingRow[]>([]);
  const [cvPorFold, setCvPorFold] = useState<CrossValFold[]>([]);
  const [cvResultados, setCvResultados] = useState<CrossValSummary[]>([]);
  const [bootstrap, setBootstrap] = useState<BootstrapRow[]>([]);
  const [mcnemar, setMcNemar] = useState<McNemarRow[]>([]);
  const [cochran, setCochran] = useState<CochranQ | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const fetchData = async () => {
    setLoading(true);
    setError("");
    try {
      const [compRes, cvRes, bootRes, mcnRes, cochRes] = await Promise.all([
        api.get<{ ranking: RankingRow[] }>("/statistics/model-comparison").catch(() => ({ data: { ranking: [], effect_size: [] } })),
        api.get<{ resultados: CrossValSummary[]; por_fold: CrossValFold[] }>("/statistics/cross-validation").catch(() => ({ data: { resultados: [], por_fold: [] } })),
        api.get<{ bootstrap_intervals: BootstrapRow[] }>("/statistics/bootstrap").catch(() => ({ data: { bootstrap_intervals: [] } })),
        api.get<{ resultados: McNemarRow[] }>("/statistics/mcnemar").catch(() => ({ data: { resultados: [], holm_posthoc: [] } })),
        api.get<{ cochran_q: CochranQ }>("/statistics/cochran").catch(() => ({ data: { cochran_q: null } })),
      ]);
      setRanking((compRes.data.ranking ?? []).map((r) => ({
        ...r,
        accuracy: Number(r.accuracy),
        precision: r.precision != null ? Number(r.precision) : undefined,
        recall: r.recall != null ? Number(r.recall) : undefined,
        f1_score: Number(r.f1_score),
        f1_macro: r.f1_macro != null ? Number(r.f1_macro) : undefined,
        mcc: r.mcc != null ? Number(r.mcc) : undefined,
      })));
      setCvPorFold((cvRes.data.por_fold ?? []).map((cv) => ({
        ...cv,
        accuracy: Number(cv.accuracy),
        f1_macro: Number(cv.f1_macro),
        mcc: cv.mcc != null ? Number(cv.mcc) : undefined,
      })));
      setBootstrap((bootRes.data.bootstrap_intervals ?? []).map((b) => ({
        ...b,
        mean: Number(b.mean),
        ci_inf: Number(b.ci_inf),
        ci_sup: Number(b.ci_sup),
      })));
      setMcNemar((mcnRes.data.resultados ?? []).map((r) => ({
        ...r,
        estadistico: Number(r.estadistico),
        p_valor: Number(r.p_valor),
      })));
      setCochran(cochRes.data.cochran_q
        ? { ...cochRes.data.cochran_q, q_statistic: Number(cochRes.data.cochran_q.q_statistic), p_value: Number(cochRes.data.cochran_q.p_value) }
        : null);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Error al cargar estadisticas");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  if (error && ranking.length === 0) {
    return <ErrorState message={error} onRetry={fetchData} />;
  }

  const flatModels: FlatModel[] = ranking.map((r) => ({
    model: r.modelo,
    accuracy: r.accuracy,
    precision: r.precision ?? 0,
    recall: r.recall ?? 0,
    f1: r.f1_score ?? r.f1_macro,
    auc: 0,
  }));

  const cvMean = cvPorFold.length > 0
    ? cvPorFold.reduce((a, c) => a + c.accuracy, 0) / cvPorFold.length
    : 0;

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">
          Estadisticas y Validacion
        </h2>
        <p className="text-muted-foreground">
          Analisis detallado del rendimiento de modelos y validacion estadistica
        </p>
      </div>

      <Tabs defaultValue="comparison">
        <TabsList>
          <TabsTrigger value="comparison">Comparacion</TabsTrigger>
          <TabsTrigger value="crossval">Validacion Cruzada</TabsTrigger>
          <TabsTrigger value="bootstrap">Bootstrap</TabsTrigger>
          <TabsTrigger value="tests">Pruebas Estadisticas</TabsTrigger>
        </TabsList>

        <TabsContent value="comparison" className="space-y-6">
          {loading && ranking.length === 0 ? (
            <div className="flex items-center justify-center py-12 text-muted-foreground">
              <Loader2 className="mr-2 h-5 w-5 animate-spin" />
              Cargando...
            </div>
          ) : flatModels.length === 0 ? (
            <p className="text-center text-muted-foreground py-8">
              No hay datos de comparacion. Ejecuta los entrenamientos desde Streamlit.
            </p>
          ) : (
            <>
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg flex items-center gap-2">
                    <Brain className="h-5 w-5 text-primary" />
                    Comparacion de Modelos
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Modelo</TableHead>
                        <TableHead>Precision</TableHead>
                        <TableHead>Precision</TableHead>
                        <TableHead>Recall</TableHead>
                        <TableHead>F1-Score</TableHead>
                        <TableHead>MCC</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {flatModels.map((m) => (
                        <TableRow key={m.model}>
                          <TableCell className="font-medium">{m.model}</TableCell>
                          <TableCell>{(m.accuracy * 100).toFixed(1)}%</TableCell>
                          <TableCell>{(m.precision * 100).toFixed(1)}%</TableCell>
                          <TableCell>{(m.recall * 100).toFixed(1)}%</TableCell>
                          <TableCell>{(m.f1 * 100).toFixed(1)}%</TableCell>
                          <TableCell>{ranking.find((r) => r.modelo === m.model)?.mcc?.toFixed(4) ?? "N/A"}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                  <div className="mt-4 p-4 bg-muted rounded-lg space-y-1">
                    <p className="text-sm font-medium flex items-center gap-2">
                      <Lightbulb className="h-4 w-4 text-amber-500" />
                      Interpretacion
                    </p>
                    <p className="text-xs text-muted-foreground">
                      Esta tabla compara las <strong>metricas principales</strong> de todos los
                      modelos entrenados. El MCC (coeficiente de correlacion de Matthews) es la
                      metrica mas importante &mdash; un valor cercano a 1 indica prediccion perfecta,
                      cercano a 0 indica rendimiento aleatorio, y negativo indica discordancia
                      sistematica. El F1-score balancea precision y recall.
                    </p>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Metricas por Modelo</CardTitle>
                </CardHeader>
                <CardContent>
                  <BarChart
                    data={flatModels.map((m) => ({
                      ...m,
                      accuracy: m.accuracy * 100,
                      f1: m.f1 * 100,
                    }))}
                    xKey="model"
                    bars={[
                      { key: "accuracy", color: "#22C55E", name: "Precision (%)" },
                      { key: "f1", color: "#166534", name: "F1 (%)" },
                    ]}
                  />
                </CardContent>
              </Card>
            </>
          )}
        </TabsContent>

        <TabsContent value="crossval" className="space-y-6">
          {loading && cvPorFold.length === 0 ? (
            <div className="flex items-center justify-center py-12 text-muted-foreground">
              <Loader2 className="mr-2 h-5 w-5 animate-spin" />
              Cargando...
            </div>
          ) : cvPorFold.length === 0 ? (
            <p className="text-center text-muted-foreground py-8">
              No hay datos de validacion cruzada. Ejecuta la validacion desde Streamlit.
            </p>
          ) : (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <CheckCircle2 className="h-5 w-5 text-green-600" />
                  Validacion Cruzada (5-Folds)
                </CardTitle>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Fold</TableHead>
                      <TableHead>Modelo</TableHead>
                      <TableHead>Precision</TableHead>
                      <TableHead>F1-Macro</TableHead>
                      <TableHead>MCC</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {cvPorFold.map((cv, i) => (
                      <TableRow key={i}>
                        <TableCell className="font-medium">{cv.fold}</TableCell>
                        <TableCell>{cv.modelo ?? "&mdash;"}</TableCell>
                        <TableCell>
                          <Badge variant="success">
                            {(cv.accuracy * 100).toFixed(1)}%
                          </Badge>
                        </TableCell>
                        <TableCell>{(cv.f1_macro * 100).toFixed(1)}%</TableCell>
                        <TableCell>{cv.mcc?.toFixed(4) ?? "N/A"}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
                <div className="mt-4 p-4 bg-muted rounded-lg">
                  <p className="text-sm text-muted-foreground">
                    Precision media:{" "}
                    <span className="font-semibold text-foreground">
                      {(cvMean * 100).toFixed(1)}%
                    </span>
                  </p>
                </div>
                <div className="mt-2 p-4 bg-muted rounded-lg space-y-1">
                  <p className="text-sm font-medium flex items-center gap-2">
                    <Lightbulb className="h-4 w-4 text-amber-500" />
                    Interpretacion
                  </p>
                  <p className="text-xs text-muted-foreground">
                    La validacion cruzada divide los datos en 5 particiones (folds) y
                    evalua el modelo 5 veces, usando cada particion como test una vez.
                    La <strong>precision media</strong> da una estimacion mas robusta del
                    rendimiento real. Una baja variacion entre folds indica que el modelo
                    es estable y no depende de una particion especifica.
                  </p>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="bootstrap" className="space-y-6">
          {loading && bootstrap.length === 0 ? (
            <div className="flex items-center justify-center py-12 text-muted-foreground">
              <Loader2 className="mr-2 h-5 w-5 animate-spin" />
              Cargando...
            </div>
          ) : bootstrap.length === 0 ? (
            <p className="text-center text-muted-foreground py-8">
              No hay intervalos bootstrap. Ejecuta la validacion estadistica desde Streamlit.
            </p>
          ) : (
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
                      <TableHead>Metrica</TableHead>
                      <TableHead>Media</TableHead>
                      <TableHead>IC Inferior</TableHead>
                      <TableHead>IC Superior</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {bootstrap.map((b, i) => (
                      <TableRow key={i}>
                        <TableCell className="font-medium">{b.modelo}</TableCell>
                        <TableCell>{b.metric}</TableCell>
                        <TableCell>{(b.mean * 100).toFixed(1)}%</TableCell>
                        <TableCell>{(b.ci_inf * 100).toFixed(1)}%</TableCell>
                        <TableCell>{(b.ci_sup * 100).toFixed(1)}%</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
                <div className="mt-4 p-4 bg-muted rounded-lg space-y-1">
                  <p className="text-sm font-medium flex items-center gap-2">
                    <Lightbulb className="h-4 w-4 text-amber-500" />
                    Interpretacion
                  </p>
                  <p className="text-xs text-muted-foreground">
                    Los intervalos de confianza bootstrap al 95% indican el rango donde se
                    encuentra la <strong>verdadera metrica</strong> con un 95% de confianza.
                    Si los intervalos de dos modelos no se superponen, es una senal de que
                    sus rendimientos son significativamente distintos. Intervalos anchos
                    indican mayor incertidumbre en la estimacion.
                  </p>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="tests" className="space-y-6">
          {loading ? (
            <div className="flex items-center justify-center py-12 text-muted-foreground">
              <Loader2 className="mr-2 h-5 w-5 animate-spin" />
              Cargando...
            </div>
          ) : (
            <>
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg flex items-center gap-2">
                    <XCircle className="h-5 w-5 text-orange-600" />
                    Prueba de McNemar
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {mcnemar.length === 0 ? (
                    <p className="text-sm text-muted-foreground">
                      No hay resultados de McNemar. Ejecuta la validacion estadistica desde Streamlit.
                    </p>
                  ) : (
                    <>
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>Modelo A vs B</TableHead>
                            <TableHead>Estadistico &chi;&sup2;</TableHead>
                            <TableHead>Valor p</TableHead>
                            <TableHead>Significancia</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {mcnemar.map((row, i) => (
                            <TableRow key={i}>
                              <TableCell>{row.comparacion}</TableCell>
                              <TableCell>{row.estadistico.toFixed(2)}</TableCell>
                              <TableCell>{row.p_valor.toFixed(4)}</TableCell>
                              <TableCell>
                                <Badge variant={row.significancia === "significativo" || row.significancia === "Significativo" ? "success" : "warning"}>
                                  {row.significancia}
                                </Badge>
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                      <div className="mt-4 p-4 bg-muted rounded-lg space-y-1">
                        <p className="text-sm font-medium flex items-center gap-2">
                          <Lightbulb className="h-4 w-4 text-amber-500" />
                          Interpretacion
                        </p>
                        <p className="text-xs text-muted-foreground">
                          La prueba de McNemar compara si dos modelos tienen diferencias significativas
                          en sus predicciones. Un <strong>valor p &lt; 0.05</strong> indica que los modelos
                          se comportan de manera distinta (significativo). Si el valor p es alto
                          (&ge; 0.05), no hay evidencia suficiente para decir que los modelos difieren.
                        </p>
                      </div>
                    </>
                  )}
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
                  {!cochran ? (
                    <p className="text-sm text-muted-foreground">
                      No hay resultados de Cochran Q. Ejecuta la validacion estadistica desde Streamlit.
                    </p>
                  ) : (
                    <>
                      <div className="p-4 bg-muted rounded-lg space-y-2">
                        <p className="text-sm">
                          <span className="font-semibold">Estadistico Q:</span>{" "}
                          {cochran.q_statistic.toFixed(2)}
                        </p>
                        <p className="text-sm">
                          <span className="font-semibold">Valor p:</span>{" "}
                          {cochran.p_value.toFixed(4)}
                        </p>
                        <p className="text-sm">
                          <span className="font-semibold">Conclusion:</span>{" "}
                          <Badge variant={cochran.p_value < 0.05 ? "success" : "warning"}>
                            {cochran.significancia}
                          </Badge>
                        </p>
                      </div>
                      <div className="mt-4 p-4 bg-muted rounded-lg space-y-1">
                        <p className="text-sm font-medium flex items-center gap-2">
                          <Lightbulb className="h-4 w-4 text-amber-500" />
                          Interpretacion
                        </p>
                        <p className="text-xs text-muted-foreground">
                          La prueba de Cochran Q evalua si <strong>todos los modelos tienen el mismo
                          rendimiento</strong> de forma simultanea. Si el valor p es &lt; 0.05,
                          se rechaza la hipotesis nula y concluimos que al menos un modelo
                          es diferente. En ese caso, el post-hoc de McNemar con correccion Holm
                          identifica que pares especificos tienen diferencias.
                        </p>
                      </div>
                    </>
                  )}
                </CardContent>
              </Card>
            </>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
