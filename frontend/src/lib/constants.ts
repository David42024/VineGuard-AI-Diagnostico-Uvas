export const CLASS_NAMES: Record<string, string> = {
  Black_rot: "Black rot",
  Esca: "Esca",
  Healthy: "Healthy",
  Leaf_blight: "Leaf blight",
};

export const CLASS_DISPLAY_NAMES: Record<string, string> = {
  Black_rot: "Black Rot",
  Esca: "Esca (Black Measles)",
  Healthy: "Healthy Leaf",
  Leaf_blight: "Leaf Blight",
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
  all: "All Models",
  consensus: "Consensus of 5 models",
  best_model: "Best Model",
};

export const MODE_LABELS: Record<string, string> = {
  consensus: "Consensus of 5 models",
  best_model: "Best Model",
  compare_all: "All Models",
  single: "Single model",
};

export const MODE_DESCRIPTIONS: Record<string, string> = {
  consensus: "Combines results from multiple models by majority voting",
  best_model: "Uses the best performing model according to benchmark evaluation",
  compare_all: "Runs all models and compares their detailed predictions",
  single: "Prediction with a specific model",
};

export function formatClassName(classCode: string): string {
  return CLASS_NAMES[classCode] || classCode.replace(/_/g, " ");
}

export function getModelName(key: string): string {
  return MODEL_NAMES[key] || key.replace(/_/g, " ");
}
