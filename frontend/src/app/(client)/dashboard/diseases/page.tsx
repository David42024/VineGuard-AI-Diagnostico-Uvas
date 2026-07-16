"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Leaf, Bug, Info, AlertTriangle, CheckCircle2 } from "lucide-react";

interface DiseaseInfo {
  id: string;
  name: string;
  scientificName: string;
  type: "fungal" | "bacterial" | "healthy";
  severity: "low" | "medium" | "high";
  icon: React.ElementType;
  description: string;
  symptoms: string[];
  recommendations: string[];
}

const diseases: DiseaseInfo[] = [
  {
    id: "healthy",
    name: "Hoja Sana",
    scientificName: "Vitis vinifera - estado saludable",
    type: "healthy",
    severity: "low",
    icon: Leaf,
    description:
      "Una hoja de vid sana presenta un color verde uniforme, textura firme y ausencia de manchas o deformaciones. Las hojas sanas son esenciales para una fotosíntesis eficiente y una buena producción de uva.",
    symptoms: [
      "Color verde uniforme en toda la superficie",
      "Textura firme y consistente",
      "Ausencia de manchas, moho o decoloración",
      "Forma regular y bien definida",
      "Nervaduras visibles pero no sobresalientes",
    ],
    recommendations: [
      "Mantener el programa de riego establecido",
      "Continuar con la fertilización balanceada",
      "Realizar monitoreo semanal preventivo",
      "Mantener la poda de mantenimiento",
      "Aplicar fungicidas preventivos según calendario",
    ],
  },
  {
    id: "black_rot",
    name: "Podredumbre Negra",
    scientificName: "Guignardia bidwellii",
    type: "fungal",
    severity: "high",
    icon: Bug,
    description:
      "Enfermedad fúngica que afecta hojas, brotes y frutos. Se caracteriza por manchas marrones circulares con bordes oscuros que pueden coalescer y causar la caída prematura de las hojas.",
    symptoms: [
      "Manchas circulares de color marrón claro a oscuro",
      "Bordes oscuros bien definidos alrededor de las lesiones",
      "Puntos negros (picnidios) visibles en el centro",
      "Amarillamiento del tejido circundante",
      "Caída prematura de hojas en casos severos",
    ],
    recommendations: [
      "Aplicar fungicidas a base de cobre o azufre",
      "Eliminar y destruir hojas infectadas",
      "Mejorar la circulación de aire mediante poda",
      "Evitar el riego por aspersión sobre el follaje",
      "Realizar monitoreo frecuente durante temporada de lluvias",
    ],
  },
  {
    id: "esca",
    name: "Esca",
    scientificName: "Phaeomoniella chlamydospora, Phaeoacremonium aleophilum",
    type: "fungal",
    severity: "high",
    icon: AlertTriangle,
    description:
      "Enfermedad de la madera de la vid que causa decaimiento progresivo. En las hojas se manifiesta como un patrón de clorosis intervenal con manchas necróticas, conocido como 'tigrado'.",
    symptoms: [
      "Clorosis intervenal (amarillamiento entre nervaduras)",
      "Manchas necróticas de color marrón rojizo",
      "Patrón característico de 'tigrado' en la hoja",
      "Bordes de las hojas enrollados hacia arriba",
      "Decaimiento general y muerte regresiva de brazos",
      "Síntomas más visibles en verano",
    ],
    recommendations: [
      "No existe cura; enfocarse en prevención",
      "Podar y eliminar brazos afectados",
      "Desinfectar herramientas de poda entre cada corte",
      "Evitar heridas innecesarias en la planta",
      "Considerar replantación en casos severos",
      "Aplicar fungicidas protectores en heridas de poda",
    ],
  },
  {
    id: "leaf_blight",
    name: "Tizón de la Hoja",
    scientificName: "Pseudocercospora vitis",
    type: "fungal",
    severity: "medium",
    icon: Bug,
    description:
      "Enfermedad foliar causada por un hongo que produce manchas angulares de color marrón oscuro a negro, generalmente limitadas por las nervaduras de la hoja.",
    symptoms: [
      "Manchas angulares pequeñas de color marrón oscuro",
      "Lesiones delimitadas por las nervaduras",
      "Color amarillo-anaranjado alrededor de las lesiones",
      "Caída prematura de hojas en infecciones severas",
      "Pérdida de vigor y reducción de la fotosíntesis",
    ],
    recommendations: [
      "Aplicar fungicidas protectantes al inicio de los síntomas",
      "Mantener el follaje seco (riego por goteo)",
      "Realizar podas para mejorar aireación",
      "Eliminar hojas infectadas del suelo",
      "Rotar fungicidas para evitar resistencias",
    ],
  },
];

export default function DiseasesPage() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">
          Enfermedades Reconocidas
        </h2>
        <p className="text-muted-foreground">
          Información sobre las enfermedades que VineGuard AI puede detectar
        </p>
      </div>

      <div className="grid gap-6">
        {diseases.map((disease) => {
          const Icon = disease.icon;
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
                      <CardTitle className="text-xl">{disease.name}</CardTitle>
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
                      {disease.type === "healthy"
                        ? "Saludable"
                        : disease.type === "fungal"
                        ? "Fúngica"
                        : "Bacteriana"}
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
                      {disease.severity === "high"
                        ? "Alta"
                        : disease.severity === "medium"
                        ? "Media"
                        : "Baja"}{" "}
                      severidad
                    </Badge>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-sm text-muted-foreground">
                  {disease.description}
                </p>

                <Separator />

                <div className="grid gap-6 md:grid-cols-2">
                  <div>
                    <h4 className="flex items-center gap-2 text-sm font-semibold mb-3">
                      <AlertTriangle className="h-4 w-4 text-red-500" />
                      Síntomas
                    </h4>
                    <ul className="space-y-2">
                      {disease.symptoms.map((symptom, i) => (
                        <li
                          key={i}
                          className="flex items-start gap-2 text-sm"
                        >
                          <span className="mt-1 block h-1.5 w-1.5 shrink-0 rounded-full bg-red-400" />
                          {symptom}
                        </li>
                      ))}
                    </ul>
                  </div>
                  <div>
                    <h4 className="flex items-center gap-2 text-sm font-semibold mb-3">
                      <CheckCircle2 className="h-4 w-4 text-green-500" />
                      Recomendaciones
                    </h4>
                    <ul className="space-y-2">
                      {disease.recommendations.map((rec, i) => (
                        <li
                          key={i}
                          className="flex items-start gap-2 text-sm"
                        >
                          <span className="mt-1 block h-1.5 w-1.5 shrink-0 rounded-full bg-green-400" />
                          {rec}
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
                ¿Cómo usar esta información?
              </p>
              <p>
                Esta guía es educativa y de referencia. Los resultados del
                diagnóstico automático deben ser verificados por un profesional.
                Si sospechas de una enfermedad en tus cultivos, contacta a un
                ingeniero agrónomo o especialista fitosanitario para una
                evaluación precisa.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
