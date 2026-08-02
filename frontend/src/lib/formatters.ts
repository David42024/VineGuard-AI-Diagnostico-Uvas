/** Centralized formatting utilities for the frontend. */

import { useThemeStore } from "@/store/theme-store";

export function formatPercentage(value: number | null | undefined): string {
  if (value == null) return "N/A";
  return `${(value * 100).toFixed(2)}%`;
}

export function formatMetric(value: number | null | undefined): string {
  if (value == null) return "N/A";
  return value.toFixed(4);
}

export function formatDate(dateStr: string | Date | null | undefined): string {
  if (!dateStr) return "—";
  const d = new Date(dateStr);
  const lang = useThemeStore.getState().language || "es";
  const locale = lang === "en" ? "en-US" : lang === "pt" ? "pt-BR" : "es-ES";
  return d.toLocaleDateString(locale, {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function formatConfidence(value: number | null | undefined): string {
  if (value == null) return "N/A";
  return `${(value * 100).toFixed(1)}%`;
}
