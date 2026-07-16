// ─── Auth ────────────────────────────────────────────────────────
export interface User {
  id: number;
  username: string;
  name: string;
  role: "admin" | "client";
  active: boolean;
}

export interface TokenResponse {
  token_type: string;
  user: User;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface UserUpdate {
  name?: string;
  username?: string;
  role?: string;
  active?: boolean;
}

// ─── Diagnosis ───────────────────────────────────────────────────
export interface PredictionInfo {
  class_code: string;
  display_name: string;
  confidence: number;
  health_status: "healthy" | "diseased" | "unknown";
  risk_level: "none" | "low" | "moderate" | "high" | "unknown";
}

export interface ModelInfoDiagnosis {
  key: string;
  name: string;
  version: string;
}

export interface ConsensusInfo {
  status: string;
  predicted_class?: string;
  confidence?: number;
  agreement_level?: string;
  agreeing_models?: number;
  total_models?: number;
}

export interface PredictionDetail {
  model_key: string;
  model_name: string;
  predicted_class: string;
  confidence?: number;
  probabilities?: number[];
  inference_time_ms?: number;
  status: string;
  error?: string;
}

export interface DiagnosisResponse {
  id: number;
  created_at?: string;
  status: string;
  is_demo: boolean;
  image_url?: string;
  prediction: PredictionInfo;
  model: ModelInfoDiagnosis;
  probabilities?: Record<string, number>;
  inference_time_ms?: number;
  consensus?: ConsensusInfo;
  predictions?: PredictionDetail[];
  warnings: string[];
}

export interface DiagnosisListItem {
  id: number;
  created_at?: string;
  filename?: string;
  result: string;
  confidence?: number;
  model_used?: string;
  inference_time_ms?: number;
  status: string;
  user_name?: string;
  username?: string;
  image_url?: string;
  is_demo: boolean;
}

export interface PaginatedDiagnoses {
  items: DiagnosisListItem[];
  total: number;
  limit: number;
  offset: number;
}

// ─── Models ──────────────────────────────────────────────────────
export interface ModelMetrics {
  accuracy?: number;
  balanced_accuracy?: number;
  precision?: number;
  recall?: number;
  f1_score?: number;
  mcc?: number;
  auc_macro?: number;
  auc_micro?: number;
}

export interface ModelInfo {
  id: string;
  name: string;
  type: string;
  status: string;
  available: boolean;
  metrics?: ModelMetrics;
  params?: Record<string, unknown>;
  reports_dir?: string;
  last_updated?: string;
}

export interface ModelRanking {
  ranking: number;
  modelo: string;
  accuracy: number;
  f1_score: number;
  mcc: number;
  acc_ci_inf: number;
  acc_ci_sup: number;
  f1_ci_inf: number;
  f1_ci_sup: number;
  mcc_ci_inf: number;
  mcc_ci_sup: number;
}

export interface BestModelResponse {
  model_name: string;
  accuracy: number;
  f1_score: number;
  mcc: number;
  selection_criteria: string;
  details?: string;
}

export interface ModelTestResponse {
  model_key: string;
  predicted_class: string;
  confidence?: number;
  probabilities?: number[];
  inference_time_ms: number;
  error?: string;
}

// ─── Reports ─────────────────────────────────────────────────────
export interface ReportItem {
  id: string;
  filename: string;
  size_bytes: number;
  created_at: string;
}

export interface ReportListResponse {
  reports: ReportItem[];
}

export interface ReportGenerateResponse {
  message: string;
  filename: string;
  path: string;
  download_url: string;
}

// ─── Statistics ──────────────────────────────────────────────────
export interface GeneralStats {
  total_diagnostics: number;
  today_diagnostics: number;
  healthy_pct: number;
  diseased_pct: number;
  total_users: number;
}

export interface SummaryResponse {
  general_stats: GeneralStats;
  disease_distribution: Record<string, number>;
  diagnostics_by_date: { date: string; count: number }[];
  best_model: string;
  ranking: { modelo: string; accuracy: number; f1_score: number; recall?: number }[];
  cross_validation: { modelo: string; accuracy_mean: number; accuracy_std: number }[];
}

// ─── Errors ──────────────────────────────────────────────────────
export interface ErrorDetail {
  code: string;
  message: string;
  details?: unknown;
}

export interface ApiError {
  error: ErrorDetail;
}
