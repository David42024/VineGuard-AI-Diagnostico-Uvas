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

export default api;
