"""Consolidated Pydantic schemas for VineGuard AI API."""
from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime


# ─── Pagination ───────────────────────────────────────────────────


class PaginatedResponse(BaseModel):
    items: list[Any]
    total: int
    limit: int
    offset: int


# ─── Error ────────────────────────────────────────────────────────


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Optional[Any] = None


class ErrorResponse(BaseModel):
    error: ErrorDetail


# ─── Auth ─────────────────────────────────────────────────────────


class LoginRequest(BaseModel):
    username: str
    password: str


class UserInfo(BaseModel):
    id: int
    username: str
    name: str
    role: str
    active: bool


class TokenResponse(BaseModel):
    token_type: str = "bearer"
    user: UserInfo


class UserResponse(BaseModel):
    id: int
    username: str
    name: str
    role: str
    active: bool


class UserUpdate(BaseModel):
    name: Optional[str] = None
    username: Optional[str] = None
    role: Optional[str] = None
    active: Optional[bool] = None


# ─── Diagnosis ────────────────────────────────────────────────────


class PredictionInfo(BaseModel):
    class_code: str
    display_name: str
    confidence: float
    health_status: str
    risk_level: str


class ModelInfoDiagnosis(BaseModel):
    key: str
    name: str
    version: str = "1.0.0"


class ConsensusInfo(BaseModel):
    status: str
    predicted_class: Optional[str] = None
    confidence: Optional[float] = None
    agreement_level: Optional[str] = None
    agreeing_models: Optional[int] = None
    total_models: Optional[int] = None


class PredictionDetail(BaseModel):
    model_config = {"protected_namespaces": ()}
    model_key: str
    model_name: str
    predicted_class: str
    confidence: Optional[float] = None
    probabilities: Optional[list[float]] = None
    inference_time_ms: Optional[float] = None
    status: str = "success"
    error: Optional[str] = None


class DiagnosisResponse(BaseModel):
    id: int
    created_at: Optional[datetime] = None
    status: str = "completed"
    is_demo: bool = False
    image_url: Optional[str] = None
    prediction: PredictionInfo
    model: ModelInfoDiagnosis
    probabilities: Optional[dict[str, float]] = None
    inference_time_ms: Optional[float] = None
    consensus: Optional[ConsensusInfo] = None
    predictions: Optional[list[PredictionDetail]] = None
    warnings: list[str] = []


class DiagnosisListItem(BaseModel):
    model_config = {"protected_namespaces": ()}
    id: int
    created_at: Optional[datetime] = None
    filename: Optional[str] = None
    result: str
    confidence: Optional[float] = None
    model_used: Optional[str] = None
    inference_time_ms: Optional[float] = None
    status: str = "completed"
    user_name: Optional[str] = None
    username: Optional[str] = None
    image_url: Optional[str] = None
    is_demo: bool = False


class PaginatedDiagnoses(BaseModel):
    items: list[DiagnosisListItem]
    total: int
    limit: int
    offset: int


# ─── Model ────────────────────────────────────────────────────────


class ModelMetrics(BaseModel):
    accuracy: Optional[float] = None
    balanced_accuracy: Optional[float] = None
    precision: Optional[float] = None
    recall: Optional[float] = None
    f1_score: Optional[float] = None
    mcc: Optional[float] = None
    auc_macro: Optional[float] = None
    auc_micro: Optional[float] = None


class ModelInfo(BaseModel):
    model_config = {"protected_namespaces": ()}
    id: str
    name: str
    type: str
    status: str = "unknown"
    available: bool = False
    metrics: Optional[ModelMetrics] = None
    params: Optional[dict[str, Any]] = None
    reports_dir: Optional[str] = None
    last_updated: Optional[datetime] = None


class ModelRanking(BaseModel):
    model_config = {"protected_namespaces": ()}
    ranking: int
    modelo: str
    accuracy: float
    f1_score: float
    mcc: float
    acc_ci_inf: float
    acc_ci_sup: float
    f1_ci_inf: float
    f1_ci_sup: float
    mcc_ci_inf: float
    mcc_ci_sup: float


class BestModelResponse(BaseModel):
    model_config = {"protected_namespaces": ()}
    model_name: str
    accuracy: float
    f1_score: float
    mcc: float
    selection_criteria: str
    details: Optional[str] = None


class ModelTestRequest(BaseModel):
    model_config = {"protected_namespaces": ()}
    model_key: str


class ModelTestResponse(BaseModel):
    model_config = {"protected_namespaces": ()}
    model_key: str
    predicted_class: str
    confidence: Optional[float] = None
    probabilities: Optional[list[float]] = None
    inference_time_ms: float
    error: Optional[str] = None


# ─── Report ───────────────────────────────────────────────────────


class ReportItem(BaseModel):
    id: str
    filename: str
    size_bytes: int
    created_at: str


class ReportListResponse(BaseModel):
    reports: list[ReportItem]


class ReportGenerateResponse(BaseModel):
    message: str
    filename: str
    path: str
    download_url: str


# ─── Statistics ───────────────────────────────────────────────────


class GeneralStats(BaseModel):
    total_diagnostics: int = 0
    today_diagnostics: int = 0
    healthy_pct: float = 0
    diseased_pct: float = 0
    total_users: int = 0


class SummaryResponse(BaseModel):
    general_stats: GeneralStats
    disease_distribution: dict[str, int] = {}
    diagnostics_by_date: list[dict[str, Any]] = []
    best_model: str = ""
    ranking: list[dict[str, Any]] = []
    cross_validation: list[dict[str, Any]] = []


# ─── Legacy aliases (backward compat) ────────────────────────────

# Keep old ErrorResponse shape for existing code that imports it
class LegacyErrorResponse(BaseModel):
    error_code: str
    message: str
    details: Optional[Any] = None
