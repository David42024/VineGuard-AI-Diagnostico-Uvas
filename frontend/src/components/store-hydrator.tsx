"use client";

import { useEffect } from "react";
import { useThemeStore } from "@/store/theme-store";

/**
 * Hidrata el store de tema (idioma / sidebar) sólo en el cliente,
 * después del primer render, para evitar errores de hidratación SSR.
 */
export function StoreHydrator() {
  useEffect(() => {
    useThemeStore.getState().hydrate();
  }, []);

  return null;
}
