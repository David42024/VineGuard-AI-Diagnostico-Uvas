"use client";

import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Search,
  Activity,
  Leaf,
  Bug,
  Clock,
  Camera,
  Lightbulb,
  ArrowRight,
} from "lucide-react";
import { MetricCard } from "@/components/dashboard/metric-card";
import { useAuthStore } from "@/store/auth-store";

const tips = [
  {
    icon: Camera,
    title: "Buena iluminación",
    description: "Fotografía la hoja con luz natural y evitar sombras.",
  },
  {
    icon: Lightbulb,
    title: "Hoja completa",
    description: "Asegúrate de capturar la hoja completa y centrada.",
  },
  {
    icon: Activity,
    title: "Fondo uniforme",
    description: "Usa un fondo claro y sin elementos distractores.",
  },
];

export default function ClientDashboard() {
  const { user } = useAuthStore();

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">
          Bienvenido, {user?.name || "Usuario"}
        </h2>
        <p className="text-muted-foreground">
          Realiza diagnósticos de hojas de vid y consulta tu historial
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          title="Diagnósticos Totales"
          value={42}
          icon={Activity}
        />
        <MetricCard
          title="Hojas Sanas"
          value="64%"
          icon={Leaf}
          trend="up"
          trendValue="+8%"
        />
        <MetricCard
          title="Enfermedades Detectadas"
          value={15}
          icon={Bug}
          trend="down"
          trendValue="-3%"
        />
        <MetricCard
          title="Último Resultado"
          value="Hace 2 horas"
          icon={Clock}
        />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card className="bg-gradient-to-br from-primary to-primary/80 text-primary-foreground">
          <CardContent className="p-8 flex flex-col items-center text-center space-y-4">
            <Search className="h-12 w-12" />
            <div>
              <h3 className="text-2xl font-bold">Nuevo Diagnóstico</h3>
              <p className="text-primary-foreground/80 mt-1">
                Sube una foto de una hoja de vid para analizarla
              </p>
            </div>
            <Link href="/dashboard/diagnosis">
              <Button
                variant="secondary"
                size="lg"
                className="mt-2"
              >
                Comenzar
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </Link>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <Camera className="h-5 w-5 text-primary" />
              Consejos para fotos
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {tips.map((tip, i) => (
              <div key={i} className="flex gap-3">
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary/10">
                  <tip.icon className="h-4 w-4 text-primary" />
                </div>
                <div>
                  <p className="text-sm font-medium">{tip.title}</p>
                  <p className="text-xs text-muted-foreground">
                    {tip.description}
                  </p>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg">Diagnósticos Recientes</CardTitle>
            <Link href="/dashboard/history">
              <Button variant="ghost" size="sm">
                Ver todos <ArrowRight className="ml-1 h-4 w-4" />
              </Button>
            </Link>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {[
              { file: "hoja_vid_01.jpg", result: "Sana", date: "Hace 2 horas", confidence: "98.5%" },
              { file: "hoja_vid_02.jpg", result: "Podredumbre Negra", date: "Ayer", confidence: "94.2%" },
              { file: "hoja_vid_03.jpg", result: "Esca", date: "Hace 3 días", confidence: "89.7%" },
            ].map((item, i) => (
              <div
                key={i}
                className="flex items-center justify-between rounded-lg border p-4"
              >
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-muted">
                    <Leaf className="h-5 w-5 text-muted-foreground" />
                  </div>
                  <div>
                    <p className="text-sm font-medium">{item.file}</p>
                    <p className="text-xs text-muted-foreground">{item.date}</p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <Badge
                    variant={
                      item.result === "Sana" ? "success" : "destructive"
                    }
                  >
                    {item.result}
                  </Badge>
                  <span className="text-sm text-muted-foreground">
                    {item.confidence}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
