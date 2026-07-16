"use client";

import { useEffect } from "react";
import { AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-background p-8">
      <div className="mx-auto max-w-md text-center space-y-6">
        <div className="flex justify-center">
          <div className="flex h-20 w-20 items-center justify-center rounded-full bg-destructive/10">
            <AlertTriangle className="h-10 w-10 text-destructive" />
          </div>
        </div>
        <h1 className="text-3xl font-bold tracking-tight">
          Algo salió mal
        </h1>
        <p className="text-muted-foreground">
          Ocurrió un error inesperado. Nuestro equipo ha sido notificado.
          Por favor, intenta de nuevo.
        </p>
        <div className="flex justify-center gap-4">
          <Button onClick={() => window.location.reload()}>
            Recargar página
          </Button>
          <Button variant="outline" onClick={reset}>
            Reintentar
          </Button>
        </div>
      </div>
    </div>
  );
}
