import axios, { AxiosError } from "axios";
import type { ErrorDetail } from "@/types/api";

// Re-export all canonical types
export type {
  User,
  TokenResponse,
  LoginRequest,
  UserUpdate,
  PredictionInfo,
  ModelInfoDiagnosis,
  ConsensusInfo,
  PredictionDetail,
  DiagnosisResponse,
  DiagnosisListItem,
  PaginatedDiagnoses,
  ModelInfo,
  ModelMetrics,
  ModelRanking,
  BestModelResponse,
  ModelTestResponse,
  ReportItem,
  ReportListResponse,
  ReportGenerateResponse,
  GeneralStats,
  SummaryResponse,
  ErrorDetail,
  ApiError,
} from "@/types/api";

// Legacy aliases for existing component imports
export type { DiagnosisResponse as Diagnosis } from "@/types/api";
export type { ConsensusInfo as Consensus } from "@/types/api";
export type { TokenResponse as LoginResponse } from "@/types/api";

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1",
  withCredentials: true,
  headers: {
    "Content-Type": "application/json",
  },
});

api.interceptors.response.use(
  (response) => response,
  (error: AxiosError<{ error: ErrorDetail }>) => {
    if (error.response?.status === 401 && typeof window !== "undefined") {
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

export default api;
