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
import { useTranslation } from "@/i18n";

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
  const t = useTranslation();
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
      setError(e instanceof Error ? e.message : t("stats.loadError"));
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
          {t("statistics.title")}
        </h2>
        <p className="text-muted-foreground">
          {t("stats.subtitle")}
        </p>
      </div>

      <Tabs defaultValue="comparison">
        <TabsList>
          <TabsTrigger value="comparison">{t("stats.tabComparison")}</TabsTrigger>
          <TabsTrigger value="crossval">{t("stats.tabCrossval")}</TabsTrigger>
          <TabsTrigger value="bootstrap">{t("stats.tabBootstrap")}</TabsTrigger>
          <TabsTrigger value="tests">{t("stats.tabTests")}</TabsTrigger>
        </TabsList>

        {/* ──────── COMPARISON TAB ──────── */}
        <TabsContent value="comparison" className="space-y-6">
          {loading && comparison.length === 0 ? (
            <div className="flex items-center justify-center py-12 text-muted-foreground">
              <Loader2 className="mr-2 h-5 w-5 animate-spin" />
              {t("common.loading")}
            </div>
          ) : comparison.length === 0 ? (
            <p className="text-center text-muted-foreground py-8">
              {t("stats.noComparison")} <code>src/evaluacion_comparativa.py</code>.
            </p>
          ) : (
            <>
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg flex items-center gap-2">
                    <Brain className="h-5 w-5 text-primary" />
                    {t("stats.modelComparison")}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>{t("common.model")}</TableHead>
                        <TableHead>{t("common.accuracy")}</TableHead>
                        <TableHead>{t("stats.balancedAccuracy")}</TableHead>
                        <TableHead>{t("stats.precisionMacro")}</TableHead>
                        <TableHead>{t("stats.recallMacro")}</TableHead>
                        <TableHead>{t("common.f1Macro")}</TableHead>
                        <TableHead>{t("common.mcc")}</TableHead>
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
                      {t("stats.interpretation")}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {t("stats.compInterpretation")}
                    </p>
                    <p className="text-xs text-muted-foreground mt-2">
                      <strong>{t("stats.balancedAccuracy")}</strong> {t("stats.balancedAccInterpretation")}
                    </p>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">{t("stats.metricsByModel")}</CardTitle>
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
                      { key: "mcc", color: "#2563EB", name: t("admin.mccPct") },
                      { key: "f1", color: "#166534", name: t("stats.f1MacroPct") },
                      { key: "accuracy", color: "#22C55E", name: t("admin.accuracyPct") },
                    ]}
                  />
                </CardContent>
              </Card>

              {effectSize.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg">{t("stats.effectSize")}</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>{t("stats.model1")}</TableHead>
                          <TableHead>{t("stats.model2")}</TableHead>
                          <TableHead>{t("stats.diffAccuracy")}</TableHead>
                          <TableHead>{t("stats.diffF1")}</TableHead>
                          <TableHead>{t("stats.diffMcc")}</TableHead>
                          <TableHead>{t("stats.oddsRatio")}</TableHead>
                          <TableHead>{t("stats.favored")}</TableHead>
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
                        {t("stats.interpretation")}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {t("stats.effectSizeInterpretation")}
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
              {t("common.loading")}
            </div>
          ) : cvResultados.length === 0 && cvPorFold.length === 0 ? (
            <p className="text-center text-muted-foreground py-8">
              {t("stats.noCv")} <code>src/cross_validation_modelos.py</code>.
            </p>
          ) : (
            <>
              {cvPorFold.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg flex items-center gap-2">
                      <CheckCircle2 className="h-5 w-5 text-green-600" />
                      {t("stats.cvFoldDetail")}
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>{t("stats.fold")}</TableHead>
                          <TableHead>{t("common.model")}</TableHead>
                          <TableHead>{t("common.accuracy")}</TableHead>
                          <TableHead>{t("common.f1Macro")}</TableHead>
                          <TableHead>{t("common.mcc")}</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {cvPorFold.map((cv, i) => (
                          <TableRow key={i}>
                            <TableCell className="font-medium">{t("stats.foldNumber").replace("{number}", String(cv.fold))}</TableCell>
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
                    <CardTitle className="text-lg">{t("stats.cvSummary")}</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-6">
                    {cvResultados.map((m) => (
                      <div key={m.modelo} className="space-y-2">
                        <h4 className="font-semibold text-sm">{m.modelo}</h4>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                          <div className="p-3 bg-muted rounded-lg">
                            <p className="text-xs text-muted-foreground">{t("stats.accuracyMean")}</p>
                            <p className="text-lg font-bold">{formatPct(m.accuracyMean)}</p>
                            <p className="text-xs text-muted-foreground">&plusmn; {formatPct(m.accuracyStd)}</p>
                          </div>
                          <div className="p-3 bg-muted rounded-lg">
                            <p className="text-xs text-muted-foreground">{t("stats.f1Mean")}</p>
                            <p className="text-lg font-bold">{formatPct(m.f1MacroMean)}</p>
                            <p className="text-xs text-muted-foreground">&plusmn; {formatPct(m.f1MacroStd)}</p>
                          </div>
                          <div className="p-3 bg-muted rounded-lg">
                            <p className="text-xs text-muted-foreground">{t("stats.mccMean")}</p>
                            <p className="text-lg font-bold">{formatDecimal(m.mccMean)}</p>
                            <p className="text-xs text-muted-foreground">&plusmn; {formatDecimal(m.mccStd)}</p>
                          </div>
                          <div className="p-3 bg-muted rounded-lg">
                            <p className="text-xs text-muted-foreground">{t("stats.folds")}</p>
                            <p className="text-lg font-bold">{m.nFolds}</p>
                          </div>
                        </div>
                      </div>
                    ))}
                    <div className="p-4 bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-800 rounded-lg">
                      <p className="text-xs text-amber-800 dark:text-amber-200">
                        <strong>{t("stats.note")}</strong> {t("stats.cvNote")}
                      </p>
                    </div>
                    <div className="p-4 bg-muted rounded-lg space-y-1">
                      <p className="text-sm font-medium flex items-center gap-2">
                        <Lightbulb className="h-4 w-4 text-amber-500" />
                        {t("stats.interpretation")}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {t("stats.cvInterpretation").replace(
                          "{folds}",
                          String(cvResultados[0]?.nFolds ?? "N")
                        )}
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
              {t("common.loading")}
            </div>
          ) : bootstrap.length === 0 ? (
            <p className="text-center text-muted-foreground py-8">
              {t("stats.noBootstrap")}{" "}
              <code>src/validacion_estadistica_modelos.py</code>.
            </p>
          ) : (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <AlertCircle className="h-5 w-5 text-blue-600" />
                  {t("stats.bootstrapTitle")}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>{t("common.model")}</TableHead>
                      <TableHead>{t("stats.accuracyMean")}</TableHead>
                      <TableHead>{t("stats.accuracyCi")}</TableHead>
                      <TableHead>{t("stats.f1Mean")}</TableHead>
                      <TableHead>{t("stats.f1Ci")}</TableHead>
                      <TableHead>{t("stats.mccMean")}</TableHead>
                      <TableHead>{t("stats.mccCi")}</TableHead>
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
                    {t("stats.interpretation")}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {t("stats.bootstrapInterpretation")}
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
              {t("common.loading")}
            </div>
          ) : (
            <>
              {/* Cochran Q */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg flex items-center gap-2">
                    <XCircle className="h-5 w-5 text-purple-600" />
                    {t("stats.cochranTitle")}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {!cochran ? (
                    <p className="text-sm text-muted-foreground">
                      {t("stats.noCochran")}{" "}
                      <code>src/validacion_estadistica_modelos.py</code>.
                    </p>
                  ) : (
                    <div className="space-y-4">
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div className="p-3 bg-muted rounded-lg">
                          <p className="text-xs text-muted-foreground">{t("stats.qStatistic")}</p>
                          <p className="text-lg font-bold">{formatDecimal(cochran.estadisticoQ, 4)}</p>
                        </div>
                        <div className="p-3 bg-muted rounded-lg">
                          <p className="text-xs text-muted-foreground">{t("stats.pValue")}</p>
                          <p className="text-lg font-bold">{formatPValue(cochran.pValue)}</p>
                        </div>
                        <div className="p-3 bg-muted rounded-lg">
                          <p className="text-xs text-muted-foreground">{t("stats.modelsK")}</p>
                          <p className="text-lg font-bold">{cochran.k}</p>
                        </div>
                        <div className="p-3 bg-muted rounded-lg">
                          <p className="text-xs text-muted-foreground">{t("stats.imagesN")}</p>
                          <p className="text-lg font-bold">{cochran.n}</p>
                        </div>
                      </div>
                      <div className="p-3 bg-muted rounded-lg">
                        <p className="text-xs text-muted-foreground">{t("stats.interpretation")}</p>
                        <p className="text-sm font-semibold">{cochran.interpretacion}</p>
                      </div>
                      <p className="text-xs text-muted-foreground">
                        {t("stats.cochranInterpretation")}
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
                    {t("stats.mcnemarTitle")}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {mcnemar.length === 0 ? (
                    <p className="text-sm text-muted-foreground">
                      {t("stats.noMcNemar")}{" "}
                      <code>src/validacion_estadistica_modelos.py</code>.
                    </p>
                  ) : (
                    <>
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>{t("stats.model1")}</TableHead>
                            <TableHead>{t("stats.model2")}</TableHead>
                            <TableHead>{t("stats.pRaw")}</TableHead>
                            <TableHead>{t("stats.pHolm")}</TableHead>
                            <TableHead>{t("stats.significant")}</TableHead>
                            <TableHead>{t("stats.favoredModel")}</TableHead>
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
                                  <Badge variant="success">{t("common.yes")}</Badge>
                                ) : (
                                  <Badge variant="secondary">{t("common.no")}</Badge>
                                )}
                              </TableCell>
                              <TableCell>
                                {row.favorecido === "Empate" ? (
                                  <span className="flex items-center gap-1 text-muted-foreground">
                                    <Minus className="h-3 w-3" /> {t("stats.tie")}
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
                        {t("stats.mcnemarConclusion")}
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
                      {t("stats.effectSize")}
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>{t("stats.model1")}</TableHead>
                          <TableHead>{t("stats.model2")}</TableHead>
                          <TableHead>{t("stats.diffAccuracy")}</TableHead>
                          <TableHead>{t("stats.diffF1")}</TableHead>
                          <TableHead>{t("stats.diffMcc")}</TableHead>
                          <TableHead>{t("stats.oddsRatio")}</TableHead>
                          <TableHead>{t("stats.favored")}</TableHead>
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
                        {t("stats.interpretation")}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {t("stats.effectSizeInterpretation2")}
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
