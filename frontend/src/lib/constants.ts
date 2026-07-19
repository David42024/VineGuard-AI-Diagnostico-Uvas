export const CLASS_NAMES: Record<string, string> = {
  Black_rot: "Black rot",
  Esca: "Esca",
  Healthy: "Healthy",
  Leaf_blight: "Leaf blight",
};

export const CLASS_DISPLAY_NAMES: Record<string, string> = {
  Black_rot: "Podredumbre Negra",
  Esca: "Esca (Sarampión Negro)",
  Healthy: "Hoja Sana",
  Leaf_blight: "Tizón de la Hoja",
};

export const CLASS_COLORS: Record<string, string> = {
  Black_rot: "text-red-600 bg-red-50 dark:bg-red-950/20",
  Esca: "text-amber-600 bg-amber-50 dark:bg-amber-950/20",
  Healthy: "text-green-600 bg-green-50 dark:bg-green-950/20",
  Leaf_blight: "text-orange-600 bg-orange-50 dark:bg-orange-950/20",
};

export const MODEL_KEYS = ["M1", "M2", "M3", "H1", "H2"] as const;
export type ModelKey = (typeof MODEL_KEYS)[number];

export const MODEL_NAMES: Record<string, string> = {
  M1: "M1 - SVM",
  M2: "M2 - Random Forest",
  M3: "M3 - KNN",
  H1: "H1 - CNN + SVM",
  H2: "H2 - MobileNetV2 + RF",
  all: "Todos los Modelos",
  consensus: "Consenso de 5 modelos",
  best_model: "Mejor Modelo",
};

export const MODE_LABELS: Record<string, string> = {
  consensus: "Consenso de 5 modelos",
  best_model: "Mejor Modelo",
  compare_all: "Todos los Modelos",
  single: "Modelo individual",
};

export const MODE_DESCRIPTIONS: Record<string, string> = {
  consensus: "Combina resultados de múltiples modelos por votación mayoritaria",
  best_model: "Usa el modelo con mejor rendimiento según la evaluación comparativa",
  compare_all: "Ejecuta todos los modelos y compara sus predicciones detalladas",
  single: "Predicción con un modelo específico",
};

export function formatClassName(classCode: string): string {
  return CLASS_NAMES[classCode] || classCode.replace(/_/g, " ");
}

export function getModelName(key: string): string {
  return MODEL_NAMES[key] || key.replace(/_/g, " ");
}
