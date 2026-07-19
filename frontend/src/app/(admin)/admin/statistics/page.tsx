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
  Minus,
} from "lucide-react";
import type {
  ModelComparisonRow,
  CrossValSummaryRow,
  CrossValFoldRow,
  BootstrapRow,
  McNemarHolmRow,
  EffectSizeRow,
  CochranQ,
} from "@/types/api";
import { statisticsApi } from "@/lib/api";

// ── Format helpers ─────────────────────────────────────────────────

function val<T>(v: T | undefined | null): v is T {
  return v !== null && v !== undefined && !Number.isNaN(Number(v));
}

function formatPct(v: number | null | undefined): string {
  if (!val(v)) return "\u2014";
  return `${(v * 100).toFixed(2)}%`;
}

function formatDecimal(v: number | null | undefined, digits = 4): string {
  if (!val(v)) return "\u2014";
  return v!.toFixed(digits);
}

function formatPValue(v: number | null | undefined): string {
  if (!val(v)) return "\u2014";
  if (v! < 0.0001) return "< 0.0001";
  return v!.toFixed(4);
}

function getF1Macro(row: ModelComparisonRow): number | null {
  return row.f1Macro;
}

function sortByMccDesc(a: ModelComparisonRow, b: ModelComparisonRow) {
  const ma = a.mcc ?? -1;
  const mb = b.mcc ?? -1;
  return mb - ma;
}

function getShortName(modelo: string): string {
  return modelo.replace(/ - .*/, "");
}

// ── Component ──────────────────────────────────────────────────────

export default function StatisticsPage() {
  const [comparison, setComparison] = useState<ModelComparisonRow[]>([]);
  const [cvResultados, setCvResultados] = useState<CrossValSummaryRow[]>([]);
  const [cvPorFold, setCvPorFold] = useState<CrossValFoldRow[]>([]);
  const [bootstrap, setBootstrap] = useState<BootstrapRow[]>([]);
  const [mcnemar, setMcNemar] = useState<McNemarHolmRow[]>([]);
  const [effectSize, setEffectSize] = useState<EffectSizeRow[]>([]);
  const [cochran, setCochran] = useState<CochranQ | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const fetchData = async () => {
    setLoading(true);
    setError("");
    try {
      const [comp, cv, boot, mcn, coch] = await Promise.all([
        statisticsApi.getModelComparison(),
        statisticsApi.getCrossValidation(),
        statisticsApi.getBootstrap(),
        statisticsApi.getMcNemar(),
        statisticsApi.getCochran(),
      ]);
      setComparison(comp.comparison ?? []);
      setEffectSize(comp.effectSize ?? []);
      setCvResultados(cv.resultados ?? []);
      setCvPorFold(cv.porFold ?? []);
      setBootstrap(boot.bootstrap ?? []);
      setMcNemar(mcn.holmPosthoc ?? []);
      setCochran(coch.cochranQ);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Error al cargar estadisticas");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  if (error && comparison.length === 0) {
    return <ErrorState message={error} onRetry={fetchData} />;
  }

  const sortedComp = [...comparison].sort(sortByMccDesc);

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

        {/* ──────── COMPARISON TAB ──────── */}
        <TabsContent value="comparison" className="space-y-6">
          {loading && comparison.length === 0 ? (
            <div className="flex items-center justify-center py-12 text-muted-foreground">
              <Loader2 className="mr-2 h-5 w-5 animate-spin" />
              Cargando...
            </div>
          ) : comparison.length === 0 ? (
            <p className="text-center text-muted-foreground py-8">
              No hay datos de comparacion. Ejecuta <code>src/evaluacion_comparativa.py</code>.
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
                        <TableHead>Accuracy</TableHead>
                        <TableHead>Balanced Accuracy</TableHead>
                        <TableHead>Precision macro</TableHead>
                        <TableHead>Recall macro</TableHead>
                        <TableHead>F1-macro</TableHead>
                        <TableHead>MCC</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {sortedComp.map((m) => (
                        <TableRow key={m.modelo}>
                          <TableCell className="font-medium">{m.modelo}</TableCell>
                          <TableCell>{formatPct(m.accuracy)}</TableCell>
                          <TableCell>{formatPct(m.balancedAccuracy)}</TableCell>
                          <TableCell>{formatPct(m.precisionMacro)}</TableCell>
                          <TableCell>{formatPct(m.recallMacro)}</TableCell>
                          <TableCell>{formatPct(getF1Macro(m))}</TableCell>
                          <TableCell className="font-mono">{formatDecimal(m.mcc)}</TableCell>
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
                      Esta tabla compara las metricas principales de todos los
                      modelos. El MCC es la metrica mas importante — un valor
                      cercano a 1 indica prediccion perfecta. F1-macro balancea
                      precision y recall por clase.
                    </p>
                    <p className="text-xs text-muted-foreground mt-2">
                      <strong>Balanced Accuracy</strong> mide el recall promedio
                      entre las clases y da el mismo peso a cada una, por lo que
                      resulta util cuando existe desbalance de datos. En este
                      analisis multiclase, Balanced Accuracy coincide con Recall
                      macro porque ambas representan el promedio del recall de
                      las clases.
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
                    data={sortedComp.map((m) => ({
                      name: getShortName(m.modelo),
                      fullName: m.modelo,
                      mcc: m.mcc != null ? +(m.mcc * 100).toFixed(1) : 0,
                      f1: getF1Macro(m) != null ? +(getF1Macro(m)! * 100).toFixed(1) : 0,
                      accuracy: m.accuracy != null ? +(m.accuracy * 100).toFixed(1) : 0,
                    }))}
                    xKey="name"
                    bars={[
                      { key: "mcc", color: "#2563EB", name: "MCC (%)" },
                      { key: "f1", color: "#166534", name: "F1-macro (%)" },
                      { key: "accuracy", color: "#22C55E", name: "Accuracy (%)" },
                    ]}
                  />
                </CardContent>
              </Card>

              {effectSize.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg">Tamano del Efecto</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Modelo 1</TableHead>
                          <TableHead>Modelo 2</TableHead>
                          <TableHead>Diff Accuracy</TableHead>
                          <TableHead>Diff F1-macro</TableHead>
                          <TableHead>Diff MCC</TableHead>
                          <TableHead>Odds Ratio</TableHead>
                          <TableHead>Favorecido</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {effectSize.map((e, i) => (
                          <TableRow key={i}>
                            <TableCell>{e.modelo1}</TableCell>
                            <TableCell>{e.modelo2}</TableCell>
                            <TableCell>{formatPct(e.diffAccuracy)}</TableCell>
                            <TableCell>{formatPct(e.diffF1Macro)}</TableCell>
                            <TableCell className="font-mono">{formatDecimal(e.diffMcc)}</TableCell>
                            <TableCell className="font-mono">{formatDecimal(e.oddsRatio, 4)}</TableCell>
                            <TableCell>
                              <Badge variant={e.favorecido === e.modelo1 ? "success" : e.favorecido === "Empate" ? "secondary" : "warning"}>
                                {e.favorecido}
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
                        Diferencias positivas favorecen al Modelo 1. El odds
                        ratio indica que tan mas frecuente es que un modelo
                        acierte cuando el otro falla. Valores &gt; 1 favorecen
                        al primer modelo.
                      </p>
                    </div>
                  </CardContent>
                </Card>
              )}
            </>
          )}
        </TabsContent>

        {/* ──────── CROSS VALIDATION TAB ──────── */}
        <TabsContent value="crossval" className="space-y-6">
          {loading && cvResultados.length === 0 && cvPorFold.length === 0 ? (
            <div className="flex items-center justify-center py-12 text-muted-foreground">
              <Loader2 className="mr-2 h-5 w-5 animate-spin" />
              Cargando...
            </div>
          ) : cvResultados.length === 0 && cvPorFold.length === 0 ? (
            <p className="text-center text-muted-foreground py-8">
              No hay datos de validacion cruzada. Ejecuta <code>src/cross_validation_modelos.py</code>.
            </p>
          ) : (
            <>
              {cvPorFold.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg flex items-center gap-2">
                      <CheckCircle2 className="h-5 w-5 text-green-600" />
                      Validacion Cruzada — Detalle por Fold
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Fold</TableHead>
                          <TableHead>Modelo</TableHead>
                          <TableHead>Accuracy</TableHead>
                          <TableHead>F1-macro</TableHead>
                          <TableHead>MCC</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {cvPorFold.map((cv, i) => (
                          <TableRow key={i}>
                            <TableCell className="font-medium">Fold {cv.fold}</TableCell>
                            <TableCell>{cv.modelo}</TableCell>
                            <TableCell>
                              <Badge variant="success">{formatPct(cv.accuracy)}</Badge>
                            </TableCell>
                            <TableCell>{formatPct(cv.f1Macro)}</TableCell>
                            <TableCell className="font-mono">{formatDecimal(cv.mcc)}</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </CardContent>
                </Card>
              )}

              {cvResultados.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg">Resumen por Modelo</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-6">
                    {cvResultados.map((m) => (
                      <div key={m.modelo} className="space-y-2">
                        <h4 className="font-semibold text-sm">{m.modelo}</h4>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                          <div className="p-3 bg-muted rounded-lg">
                            <p className="text-xs text-muted-foreground">Accuracy media</p>
                            <p className="text-lg font-bold">{formatPct(m.accuracyMean)}</p>
                            <p className="text-xs text-muted-foreground">&plusmn; {formatPct(m.accuracyStd)}</p>
                          </div>
                          <div className="p-3 bg-muted rounded-lg">
                            <p className="text-xs text-muted-foreground">F1-macro medio</p>
                            <p className="text-lg font-bold">{formatPct(m.f1MacroMean)}</p>
                            <p className="text-xs text-muted-foreground">&plusmn; {formatPct(m.f1MacroStd)}</p>
                          </div>
                          <div className="p-3 bg-muted rounded-lg">
                            <p className="text-xs text-muted-foreground">MCC medio</p>
                            <p className="text-lg font-bold">{formatDecimal(m.mccMean)}</p>
                            <p className="text-xs text-muted-foreground">&plusmn; {formatDecimal(m.mccStd)}</p>
                          </div>
                          <div className="p-3 bg-muted rounded-lg">
                            <p className="text-xs text-muted-foreground">Folds</p>
                            <p className="text-lg font-bold">{m.nFolds}</p>
                          </div>
                        </div>
                      </div>
                    ))}
                    <div className="p-4 bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-800 rounded-lg">
                      <p className="text-xs text-amber-800 dark:text-amber-200">
                        <strong>Nota:</strong> La validacion cruzada se realizo
                        sobre TRAIN. No corresponde a la evaluacion final sobre
                        TEST. Las metricas sobre TEST se encuentran en la pestana
                        Comparacion.
                      </p>
                    </div>
                    <div className="p-4 bg-muted rounded-lg space-y-1">
                      <p className="text-sm font-medium flex items-center gap-2">
                        <Lightbulb className="h-4 w-4 text-amber-500" />
                        Interpretacion
                      </p>
                      <p className="text-xs text-muted-foreground">
                        La validacion cruzada divide los datos en {cvResultados[0]?.nFolds ?? "N"} particiones
                        y evalua cada modelo en cada particion. La media y desviacion
                        estandar resumen su estabilidad: baja desviacion indica
                        rendimiento consistente entre folds.
                      </p>
                    </div>
                  </CardContent>
                </Card>
              )}
            </>
          )}
        </TabsContent>

        {/* ──────── BOOTSTRAP TAB ──────── */}
        <TabsContent value="bootstrap" className="space-y-6">
          {loading && bootstrap.length === 0 ? (
            <div className="flex items-center justify-center py-12 text-muted-foreground">
              <Loader2 className="mr-2 h-5 w-5 animate-spin" />
              Cargando...
            </div>
          ) : bootstrap.length === 0 ? (
            <p className="text-center text-muted-foreground py-8">
              No hay intervalos bootstrap. Ejecuta{" "}
              <code>src/validacion_estadistica_modelos.py</code>.
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
                      <TableHead>Accuracy media</TableHead>
                      <TableHead>Accuracy IC 95%</TableHead>
                      <TableHead>F1-macro medio</TableHead>
                      <TableHead>F1-macro IC 95%</TableHead>
                      <TableHead>MCC medio</TableHead>
                      <TableHead>MCC IC 95%</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {[...bootstrap]
                      .sort((a, b) => (b.mccMean ?? 0) - (a.mccMean ?? 0))
                      .map((b, i) => (
                        <TableRow key={i}>
                          <TableCell className="font-medium">{b.modelo}</TableCell>
                          <TableCell>{formatPct(b.accuracyMean)}</TableCell>
                          <TableCell className="font-mono text-xs">
                            [{formatPct(b.accuracyCiLow)}, {formatPct(b.accuracyCiHigh)}]
                          </TableCell>
                          <TableCell>{formatPct(b.f1MacroMean)}</TableCell>
                          <TableCell className="font-mono text-xs">
                            [{formatPct(b.f1MacroCiLow)}, {formatPct(b.f1MacroCiHigh)}]
                          </TableCell>
                          <TableCell className="font-mono">{formatDecimal(b.mccMean)}</TableCell>
                          <TableCell className="font-mono text-xs">
                            [{formatDecimal(b.mccCiLow)}, {formatDecimal(b.mccCiHigh)}]
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
                    Los intervalos bootstrap al 95% indican el rango donde se
                    encuentra la metrica real con un 95% de confianza.
                    Intervalos con poca superposicion pueden sugerir diferencias,
                    pero la significancia formal debe consultarse en Cochran Q y
                    McNemar + Holm.
                  </p>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* ──────── STATISTICAL TESTS TAB ──────── */}
        <TabsContent value="tests" className="space-y-6">
          {loading && !cochran && mcnemar.length === 0 && effectSize.length === 0 ? (
            <div className="flex items-center justify-center py-12 text-muted-foreground">
              <Loader2 className="mr-2 h-5 w-5 animate-spin" />
              Cargando...
            </div>
          ) : (
            <>
              {/* Cochran Q */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg flex items-center gap-2">
                    <XCircle className="h-5 w-5 text-purple-600" />
                    Prueba de Cochran Q
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {!cochran ? (
                    <p className="text-sm text-muted-foreground">
                      No hay resultados de Cochran Q. Ejecuta{" "}
                      <code>src/validacion_estadistica_modelos.py</code>.
                    </p>
                  ) : (
                    <div className="space-y-4">
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div className="p-3 bg-muted rounded-lg">
                          <p className="text-xs text-muted-foreground">Estadistico Q</p>
                          <p className="text-lg font-bold">{formatDecimal(cochran.estadisticoQ, 4)}</p>
                        </div>
                        <div className="p-3 bg-muted rounded-lg">
                          <p className="text-xs text-muted-foreground">Valor p</p>
                          <p className="text-lg font-bold">{formatPValue(cochran.pValue)}</p>
                        </div>
                        <div className="p-3 bg-muted rounded-lg">
                          <p className="text-xs text-muted-foreground">Modelos (k)</p>
                          <p className="text-lg font-bold">{cochran.k}</p>
                        </div>
                        <div className="p-3 bg-muted rounded-lg">
                          <p className="text-xs text-muted-foreground">Imagenes (n)</p>
                          <p className="text-lg font-bold">{cochran.n}</p>
                        </div>
                      </div>
                      <div className="p-3 bg-muted rounded-lg">
                        <p className="text-xs text-muted-foreground">Interpretacion</p>
                        <p className="text-sm font-semibold">{cochran.interpretacion}</p>
                      </div>
                      <p className="text-xs text-muted-foreground">
                        La prueba de Cochran Q evalua si todos los modelos tienen
                        el mismo rendimiento de forma simultanea. Si el valor p es
                        &lt; 0.05, se rechaza la hipotesis nula. En ese caso, el
                        post-hoc de McNemar con correccion Holm identifica que
                        pares tienen diferencias.
                      </p>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* McNemar + Holm */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg flex items-center gap-2">
                    <XCircle className="h-5 w-5 text-orange-600" />
                    McNemar + Holm (Post-hoc)
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {mcnemar.length === 0 ? (
                    <p className="text-sm text-muted-foreground">
                      No hay resultados de McNemar. Ejecuta{" "}
                      <code>src/validacion_estadistica_modelos.py</code>.
                    </p>
                  ) : (
                    <>
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>Modelo 1</TableHead>
                            <TableHead>Modelo 2</TableHead>
                            <TableHead>Valor p original</TableHead>
                            <TableHead>Valor p ajustado (Holm)</TableHead>
                            <TableHead>Significativo</TableHead>
                            <TableHead>Modelo favorecido</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {mcnemar.map((row, i) => (
                            <TableRow key={i}>
                              <TableCell>{row.modelo1}</TableCell>
                              <TableCell>{row.modelo2}</TableCell>
                              <TableCell className="font-mono">{formatPValue(row.pRaw)}</TableCell>
                              <TableCell className="font-mono">{formatPValue(row.pHolm)}</TableCell>
                              <TableCell>
                                {row.significativo ? (
                                  <Badge variant="success">Si</Badge>
                                ) : (
                                  <Badge variant="secondary">No</Badge>
                                )}
                              </TableCell>
                              <TableCell>
                                {row.favorecido === "Empate" ? (
                                  <span className="flex items-center gap-1 text-muted-foreground">
                                    <Minus className="h-3 w-3" /> Empate
                                  </span>
                                ) : (
                                  <Badge variant={row.favorecido === row.modelo1 ? "success" : "warning"}>
                                    {row.favorecido}
                                  </Badge>
                                )}
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                      <p className="text-xs text-muted-foreground mt-4">
                        La conclusion se basa en el valor p ajustado por Holm
                        (p_holm), no en el valor p original. "Favorecido" se
                        determina por la discordancia b vs c en la tabla de
                        McNemar.
                      </p>
                    </>
                  )}
                </CardContent>
              </Card>

              {/* Effect Size (already shown in comparison tab if available, but also relevant here) */}
              {effectSize.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg flex items-center gap-2">
                      <Brain className="h-5 w-5 text-cyan-600" />
                      Tamano del Efecto
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Modelo 1</TableHead>
                          <TableHead>Modelo 2</TableHead>
                          <TableHead>Diff Accuracy</TableHead>
                          <TableHead>Diff F1-macro</TableHead>
                          <TableHead>Diff MCC</TableHead>
                          <TableHead>Odds Ratio</TableHead>
                          <TableHead>Favorecido</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {effectSize.map((e, i) => (
                          <TableRow key={i}>
                            <TableCell>{e.modelo1}</TableCell>
                            <TableCell>{e.modelo2}</TableCell>
                            <TableCell>{formatPct(e.diffAccuracy)}</TableCell>
                            <TableCell>{formatPct(e.diffF1Macro)}</TableCell>
                            <TableCell className="font-mono">{formatDecimal(e.diffMcc)}</TableCell>
                            <TableCell className="font-mono">{formatDecimal(e.oddsRatio, 4)}</TableCell>
                            <TableCell>
                              <Badge variant={e.favorecido === e.modelo1 ? "success" : e.favorecido === "Empate" ? "secondary" : "warning"}>
                                {e.favorecido}
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
                        El tamano del efecto complementa las pruebas de hipotesis.
                        Una diferencia grande en MCC sugiere una mejora practica
                        relevante, incluso si la significancia estadistica es
                        marginal.
                      </p>
                    </div>
                  </CardContent>
                </Card>
              )}
            </>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
