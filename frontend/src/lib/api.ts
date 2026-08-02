import axios, { AxiosError } from "axios";
import type { ErrorDetail, ModelInfo, ModelRanking, BestModelResponse } from "@/types/api";

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

// Tipos para el chatbot
export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export interface ChatRequest {
  messages: ChatMessage[];
  language?: string;
}

export interface ChatResponse {
  response: string;
}

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

// Funciones del chatbot
export const chatbotApi = {
  sendMessage: async (request: ChatRequest): Promise<ChatResponse> => {
    const response = await api.post<ChatResponse>("/chatbot/chat", request);
    return response.data;
  },
};

// Funciones de modelos
export const modelsApi = {
  list: async (): Promise<ModelInfo[]> => {
    const response = await api.get<ModelInfo[]>("/models");
    return response.data;
  },
  getRanking: async (): Promise<ModelRanking[]> => {
    const response = await api.get<ModelRanking[]>("/models/ranking");
    return response.data;
  },
  getBest: async (): Promise<BestModelResponse> => {
    const response = await api.get<BestModelResponse>("/models/best");
    return response.data;
  },
};

// Funciones de estadisticas
export interface ModelComparisonResponse {
  comparison: import("@/types/api").ModelComparisonRow[];
  effectSize: import("@/types/api").EffectSizeRow[];
}

export interface CrossValidationResponse {
  resultados: import("@/types/api").CrossValSummaryRow[];
  porFold: import("@/types/api").CrossValFoldRow[];
}

export interface BootstrapResponse {
  bootstrap: import("@/types/api").BootstrapRow[];
}

export interface McNemarResponse {
  holmPosthoc: import("@/types/api").McNemarHolmRow[];
}

export interface CochranResponse {
  cochranQ: import("@/types/api").CochranQ | null;
}

export const statisticsApi = {
  getModelComparison: async (): Promise<ModelComparisonResponse> => {
    const response = await api.get<ModelComparisonResponse>("/statistics/model-comparison");
    return response.data;
  },
  getCrossValidation: async (): Promise<CrossValidationResponse> => {
    const response = await api.get<CrossValidationResponse>("/statistics/cross-validation");
    return response.data;
  },
  getBootstrap: async (): Promise<BootstrapResponse> => {
    const response = await api.get<BootstrapResponse>("/statistics/bootstrap");
    return response.data;
  },
  getMcNemar: async (): Promise<McNemarResponse> => {
    const response = await api.get<McNemarResponse>("/statistics/mcnemar");
    return response.data;
  },
  getCochran: async (): Promise<CochranResponse> => {
    const response = await api.get<CochranResponse>("/statistics/cochran");
    return response.data;
  },
};

export default api;

// Devuelve el origen del API. Con NEXT_PUBLIC_API_URL relativo ("/api/v1",
// produccion) new URL(...).origin falla; en ese caso se usa el origen actual.
export function getApiOrigin(): string {
  const baseURL = api.defaults.baseURL as string;
  if (baseURL && baseURL.startsWith("http")) {
    try {
      return new URL(baseURL).origin;
    } catch {
      // Continuar con el origen del navegador
    }
  }
  return typeof window !== "undefined" ? window.location.origin : "";
}
