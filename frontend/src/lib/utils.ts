import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(date: string | Date): string {
  const d = new Date(date);
  return d.toLocaleDateString("es-ES", {
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
  if (confidence >= 0.9) return { label: "Muy Alto", color: "text-red-600" };
  if (confidence >= 0.7) return { label: "Alto", color: "text-orange-600" };
  if (confidence >= 0.5) return { label: "Medio", color: "text-yellow-600" };
  return { label: "Bajo", color: "text-green-600" };
}
