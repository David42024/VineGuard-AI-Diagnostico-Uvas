"use client";

import { Sprout, Leaf, Wheat } from "lucide-react";
import { LoginForm } from "@/components/auth/login-form";

export default function LoginPage() {
  return (
    <div className="flex min-h-screen">
      <div className="hidden lg:flex lg:w-1/2 flex-col items-center justify-center relative overflow-hidden bg-gradient-to-br from-green-900 via-green-800 to-emerald-900 p-12">
        <div className="absolute inset-0 opacity-10">
          <div className="absolute top-10 left-10">
            <Leaf className="h-32 w-32 text-green-200" />
          </div>
          <div className="absolute bottom-10 right-10">
            <Wheat className="h-40 w-40 text-green-200" />
          </div>
          <div className="absolute top-1/2 right-1/4">
            <Sprout className="h-24 w-24 text-green-300" />
          </div>
        </div>
        <div className="relative z-10 text-center space-y-6 max-w-lg">
          <div className="flex justify-center">
            <div className="flex h-20 w-20 items-center justify-center rounded-2xl bg-white/10 backdrop-blur">
              <Sprout className="h-12 w-12 text-white" />
            </div>
          </div>
          <h1 className="text-4xl font-bold text-white">VineGuard AI</h1>
          <p className="text-xl text-green-100">
            Diagnóstico inteligente para la protección temprana de cultivos de
            vid.
          </p>
          <div className="grid grid-cols-3 gap-4 pt-8">
            <div className="rounded-xl bg-white/10 p-4 backdrop-blur">
              <Leaf className="mx-auto mb-2 h-8 w-8 text-green-300" />
              <p className="text-sm text-green-100">Detección precisa</p>
            </div>
            <div className="rounded-xl bg-white/10 p-4 backdrop-blur">
              <Sprout className="mx-auto mb-2 h-8 w-8 text-green-300" />
              <p className="text-sm text-green-100">Múltiples modelos</p>
            </div>
            <div className="rounded-xl bg-white/10 p-4 backdrop-blur">
              <Wheat className="mx-auto mb-2 h-8 w-8 text-green-300" />
              <p className="text-sm text-green-100">Resultados rápidos</p>
            </div>
          </div>
        </div>
      </div>

      <div className="flex w-full lg:w-1/2 items-center justify-center p-8 bg-background">
        <LoginForm />
      </div>
    </div>
  );
}
