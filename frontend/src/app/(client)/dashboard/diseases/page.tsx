"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Leaf, Bug, Info, AlertTriangle, CheckCircle2 } from "lucide-react";
import { useTranslation } from "@/i18n";

interface DiseaseInfo {
  id: string;
  nameKey: string;
  scientificName: string;
  type: "fungal" | "bacterial" | "healthy";
  severity: "low" | "medium" | "high";
  icon: React.ElementType;
  descriptionKey: string;
  symptomKeys: string[];
  recommendationKeys: string[];
}

const diseaseData: DiseaseInfo[] = [
  {
    id: "healthy",
    nameKey: "disease.display_healthy",
    scientificName: "Vitis vinifera - estado saludable",
    type: "healthy",
    severity: "low",
    icon: Leaf,
    descriptionKey: "disease.healthy.desc",
    symptomKeys: [
      "disease.healthy.symptom1",
      "disease.healthy.symptom2",
      "disease.healthy.symptom3",
      "disease.healthy.symptom4",
      "disease.healthy.symptom5",
    ],
    recommendationKeys: [
      "disease.healthy.rec1",
      "disease.healthy.rec2",
      "disease.healthy.rec3",
      "disease.healthy.rec4",
      "disease.healthy.rec5",
    ],
  },
  {
    id: "black_rot",
    nameKey: "disease.display_black_rot",
    scientificName: "Guignardia bidwellii",
    type: "fungal",
    severity: "high",
    icon: Bug,
    descriptionKey: "disease.black_rot.desc",
    symptomKeys: [
      "disease.black_rot.symptom1",
      "disease.black_rot.symptom2",
      "disease.black_rot.symptom3",
      "disease.black_rot.symptom4",
      "disease.black_rot.symptom5",
    ],
    recommendationKeys: [
      "disease.black_rot.rec1",
      "disease.black_rot.rec2",
      "disease.black_rot.rec3",
      "disease.black_rot.rec4",
      "disease.black_rot.rec5",
    ],
  },
  {
    id: "esca",
    nameKey: "disease.esca",
    scientificName: "Phaeomoniella chlamydospora, Phaeoacremonium aleophilum",
    type: "fungal",
    severity: "high",
    icon: AlertTriangle,
    descriptionKey: "disease.esca.desc",
    symptomKeys: [
      "disease.esca.symptom1",
      "disease.esca.symptom2",
      "disease.esca.symptom3",
      "disease.esca.symptom4",
      "disease.esca.symptom5",
      "disease.esca.symptom6",
    ],
    recommendationKeys: [
      "disease.esca.rec1",
      "disease.esca.rec2",
      "disease.esca.rec3",
      "disease.esca.rec4",
      "disease.esca.rec5",
      "disease.esca.rec6",
    ],
  },
  {
    id: "leaf_blight",
    nameKey: "disease.display_leaf_blight",
    scientificName: "Pseudocercospora vitis",
    type: "fungal",
    severity: "medium",
    icon: Bug,
    descriptionKey: "disease.leaf_blight.desc",
    symptomKeys: [
      "disease.leaf_blight.symptom1",
      "disease.leaf_blight.symptom2",
      "disease.leaf_blight.symptom3",
      "disease.leaf_blight.symptom4",
      "disease.leaf_blight.symptom5",
    ],
    recommendationKeys: [
      "disease.leaf_blight.rec1",
      "disease.leaf_blight.rec2",
      "disease.leaf_blight.rec3",
      "disease.leaf_blight.rec4",
      "disease.leaf_blight.rec5",
    ],
  },
];

export default function DiseasesPage() {
  const t = useTranslation();

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">
          {t("diseases.title")}
        </h2>
        <p className="text-muted-foreground">
          {t("diseases.subtitle")}
        </p>
      </div>

      <div className="grid gap-6">
        {diseaseData.map((disease) => {
          const Icon = disease.icon;
          const typeLabel =
            disease.type === "healthy"
              ? t("diseases.type.healthy")
              : disease.type === "fungal"
              ? t("diseases.type.fungal")
              : t("diseases.type.bacterial");
          const severityLabel =
            disease.severity === "high"
              ? t("diseases.severity.high")
              : disease.severity === "medium"
              ? t("diseases.severity.medium")
              : t("diseases.severity.low");
          return (
            <Card key={disease.id} className="overflow-hidden">
              <div
                className={`h-2 ${
                  disease.type === "healthy"
                    ? "bg-green-500"
                    : disease.type === "fungal"
                    ? "bg-red-500"
                    : "bg-yellow-500"
                }`}
              />
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <div
                      className={`flex h-12 w-12 items-center justify-center rounded-xl ${
                        disease.type === "healthy"
                          ? "bg-green-100 dark:bg-green-900"
                          : "bg-red-100 dark:bg-red-900"
                      }`}
                    >
                      <Icon
                        className={`h-6 w-6 ${
                          disease.type === "healthy"
                            ? "text-green-600 dark:text-green-300"
                            : "text-red-600 dark:text-red-300"
                        }`}
                      />
                    </div>
                    <div>
                      <CardTitle className="text-xl">{t(disease.nameKey)}</CardTitle>
                      <p className="text-sm text-muted-foreground italic">
                        {disease.scientificName}
                      </p>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <Badge
                      variant={
                        disease.type === "healthy"
                          ? "success"
                          : disease.type === "fungal"
                          ? "destructive"
                          : "warning"
                      }
                    >
                      {typeLabel}
                    </Badge>
                    <Badge
                      variant={
                        disease.severity === "high"
                          ? "destructive"
                          : disease.severity === "medium"
                          ? "warning"
                          : "success"
                      }
                    >
                      {severityLabel} {t("diseases.severityWord")}
                    </Badge>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-sm text-muted-foreground">
                  {t(disease.descriptionKey)}
                </p>

                <Separator />

                <div className="grid gap-6 md:grid-cols-2">
                  <div>
                    <h4 className="flex items-center gap-2 text-sm font-semibold mb-3">
                      <AlertTriangle className="h-4 w-4 text-red-500" />
                      {t("diseases.symptoms")}
                    </h4>
                    <ul className="space-y-2">
                      {disease.symptomKeys.map((key, i) => (
                        <li
                          key={i}
                          className="flex items-start gap-2 text-sm"
                        >
                          <span className="mt-1 block h-1.5 w-1.5 shrink-0 rounded-full bg-red-400" />
                          {t(key)}
                        </li>
                      ))}
                    </ul>
                  </div>
                  <div>
                    <h4 className="flex items-center gap-2 text-sm font-semibold mb-3">
                      <CheckCircle2 className="h-4 w-4 text-green-500" />
                      {t("diseases.recommendations")}
                    </h4>
                    <ul className="space-y-2">
                      {disease.recommendationKeys.map((key, i) => (
                        <li
                          key={i}
                          className="flex items-start gap-2 text-sm"
                        >
                          <span className="mt-1 block h-1.5 w-1.5 shrink-0 rounded-full bg-green-400" />
                          {t(key)}
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      <Card className="bg-muted/50">
        <CardContent className="p-6">
          <div className="flex items-start gap-3">
            <Info className="h-5 w-5 text-primary shrink-0 mt-0.5" />
            <div className="text-sm text-muted-foreground">
              <p className="font-semibold text-foreground mb-1">
                {t("diseases.howToTitle")}
              </p>
              <p>
                {t("diseases.howToDesc")}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
