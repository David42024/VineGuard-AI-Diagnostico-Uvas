"use client";

import Link from "next/link";
import { ShieldAlert } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function UnauthorizedPage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-background p-8">
      <div className="mx-auto max-w-md text-center space-y-6">
        <div className="flex justify-center">
          <div className="flex h-20 w-20 items-center justify-center rounded-full bg-destructive/10">
            <ShieldAlert className="h-10 w-10 text-destructive" />
          </div>
        </div>
        <h1 className="text-3xl font-bold tracking-tight">
          Acceso no autorizado
        </h1>
        <p className="text-muted-foreground">
          No tienes los permisos necesarios para acceder a esta página. Si crees
          que esto es un error, contacta al administrador del sistema.
        </p>
        <div className="flex justify-center gap-4">
          <Link href="/dashboard">
            <Button variant="outline">Ir al Dashboard</Button>
          </Link>
          <Link href="/login">
            <Button>Iniciar Sesión</Button>
          </Link>
        </div>
      </div>
    </div>
  );
}
