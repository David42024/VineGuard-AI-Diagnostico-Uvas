import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";
import { useThemeStore } from "@/store/theme-store";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(date: string | Date): string {
  const d = new Date(date);
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

export function formatConfidence(value: number): string {
  return `${(value * 100).toFixed(1)}%`;
}

export function getRiskLevel(confidence: number): {
  label: string;
  color: string;
} {
  if (confidence >= 0.9) return { label: "Very High", color: "text-red-600" };
  if (confidence >= 0.7) return { label: "High", color: "text-orange-600" };
  if (confidence >= 0.5) return { label: "Medium", color: "text-yellow-600" };
  return { label: "Low", color: "text-green-600" };
}
