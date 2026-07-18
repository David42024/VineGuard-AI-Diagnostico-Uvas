"use client";

import { CheckCircle2, XCircle, MinusCircle } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
import { cn, formatConfidence } from "@/lib/utils";
import type { Consensus } from "@/lib/api";

interface ConsensusViewProps {
  consensus: Consensus;
}

export function ConsensusView({ consensus }: ConsensusViewProps) {
  const {
    agreement_level,
    predicted_class,
    agreeing_models,
    total_models,
  } = consensus;

  const agreementPercent =
    agreeing_models != null && total_models != null && total_models > 0
      ? (agreeing_models / total_models) * 100
      : 0;
  const highAgreement = agreementPercent >= 80;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-lg">
          Resultado por Consenso
          <Badge variant={highAgreement ? "success" : "warning"}>
            {agreementPercent.toFixed(0)}% acuerdo
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span>Nivel de acuerdo</span>
            <span className="font-semibold">{agreementPercent.toFixed(1)}%</span>
          </div>
          <Progress value={agreementPercent} />
        </div>

        <p className="text-sm text-muted-foreground">
          Clase final determinada:{" "}
          <span className="font-semibold text-foreground">
            {predicted_class || "N/A"}
          </span>
        </p>

        <p className="text-xs text-muted-foreground">
          {agreeing_models ?? 0} de {total_models ?? 0} modelos
          coinciden en el resultado
        </p>

        {!highAgreement && (
          <div className="flex items-start gap-2 rounded-md bg-yellow-50 p-3 text-sm text-yellow-800 dark:bg-yellow-950 dark:text-yellow-200">
            <MinusCircle className="mt-0.5 h-4 w-4 shrink-0" />
            <span>
              El nivel de acuerdo entre modelos es bajo. Se recomienda realizar
              un análisis adicional o consultar a un especialista.
            </span>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
