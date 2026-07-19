"use client";

import { CheckCircle2, MinusCircle, Users } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
import { formatConfidence } from "@/lib/utils";
import type { ConsensusInfo } from "@/types/api";
import { formatClassName, MODEL_NAMES } from "@/lib/constants";

interface ConsensusViewProps {
  consensus: ConsensusInfo;
}

export function ConsensusView({ consensus }: ConsensusViewProps) {
  const {
    agreement_level,
    predicted_class,
    agreeing_models,
    total_models,
    confidence,
    confidence_description,
    vote_distribution,
    tie_breaker,
  } = consensus;

  const agreementPercent =
    agreeing_models != null && total_models != null && total_models > 0
      ? (agreeing_models / total_models) * 100
      : 0;
  const highAgreement = agreementPercent >= 80;
  const fullAgreement = agreementPercent === 100;
  const disagreeCount =
    total_models != null && agreeing_models != null
      ? total_models - agreeing_models
      : 0;

  const agreementLabel =
    agreement_level === "high"
      ? "Alto"
      : agreement_level === "medium"
        ? "Medio"
        : "Bajo";

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-lg">
          <Users className="h-5 w-5 text-primary" />
          Resultado por consenso
          <Badge
            variant={
              fullAgreement
                ? "success"
                : highAgreement
                  ? "default"
                  : "warning"
            }
          >
            {agreementPercent.toFixed(0)}% de acuerdo
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="rounded-md bg-muted/50 p-3 space-y-2">
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">Clase final</span>
            <span className="font-semibold">
              {predicted_class
                ? formatClassName(predicted_class)
                : "N/A"}
            </span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">
              Confianza del consenso
            </span>
            <span className="font-semibold">
              {confidence != null ? formatConfidence(confidence) : "N/A"}
            </span>
          </div>
          {confidence_description && (
            <p className="text-xs text-muted-foreground italic">
              {confidence_description}
            </p>
          )}
        </div>

        <Separator />

        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">Nivel de acuerdo</span>
            <span className="font-semibold">{agreementLabel}</span>
          </div>
          <Progress
            value={agreementPercent}
            className={fullAgreement ? "bg-green-200" : ""}
          />
          <p className="text-sm text-muted-foreground">
            {fullAgreement
              ? `${agreeing_models ?? 0} de ${total_models ?? 0} modelos coinciden`
              : `${agreeing_models ?? 0} de ${total_models ?? 0} modelos coinciden en ${formatClassName(predicted_class || "")}`
            }
            {disagreeCount > 0 && (
              <span className="text-yellow-600">
                {" "}
                ({disagreeCount} modelo{disagreeCount > 1 ? "s" : ""} discrepa
                {disagreeCount === 1 ? "" : "n"})
              </span>
            )}
          </p>
        </div>

        {vote_distribution && Object.keys(vote_distribution).length > 0 && (
          <>
            <Separator />
            <div className="space-y-2">
              <p className="text-sm font-medium text-muted-foreground">
                Votos por clase
              </p>
              {Object.entries(vote_distribution)
                .sort(([, a], [, b]) => b - a)
                .map(([cls, votes]) => {
                  const pct =
                    total_models && total_models > 0
                      ? (votes / total_models) * 100
                      : 0;
                  const isWinner = cls === predicted_class;
                  return (
                    <div key={cls} className="flex items-center gap-2 text-sm">
                      <span className="w-28 truncate font-medium">
                        {formatClassName(cls)}
                      </span>
                      <div className="flex-1 bg-muted rounded-full h-2">
                        <div
                          className={`h-2 rounded-full transition-all ${
                            isWinner
                              ? "bg-green-500"
                              : "bg-muted-foreground/30"
                          }`}
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                      <span className="w-16 text-right text-muted-foreground">
                        {votes}/{total_models}
                      </span>
                      {isWinner && (
                        <CheckCircle2 className="h-4 w-4 text-green-600 shrink-0" />
                      )}
                    </div>
                  );
                })}
            </div>
          </>
        )}

        {tie_breaker && (
          <div className="rounded-md bg-yellow-50 dark:bg-yellow-950/20 p-3 text-sm text-yellow-800 dark:text-yellow-200">
            <p className="font-medium mb-1">Criterio de desempate</p>
            <p className="text-xs">{tie_breaker}</p>
          </div>
        )}

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
