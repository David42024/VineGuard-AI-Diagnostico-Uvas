"""
VineGuard AI - Sistema de Diagnóstico de Enfermedades en Uvas
Entry point - coordinates modules and routing.
"""

import sys
from pathlib import Path

_SRC_PATH = Path(__file__).resolve().parent / "src"
if str(_SRC_PATH) not in sys.path:
    sys.path.insert(0, str(_SRC_PATH))

import streamlit as st
import pandas as pd
from pathlib import Path

# ─── UI Modules ────────────────────────────────────────────────────────────
from ui.theme import render_theme
from ui.auth import render_login, init_auth
from ui.layout import render_sidebar, render_header

from ui.admin_dashboard import render as admin_dashboard
from ui.client_dashboard import render as client_dashboard
from ui.diagnosis_view import render as diagnosis_view
from ui.history_view import render as history_view
from ui.models_view import render as models_view
from ui.pipeline_view import render as pipeline_view
from ui.statistics_view import render as statistics_view
from ui.reports_view import render as reports_view
from ui.info_view import render as info_view

# ─── Database ──────────────────────────────────────────────────────────────
from database.repository import init_database

# ─── Shared prediction ─────────────────────────────────────────────────────
from predecir_imagen import cargar_modelo
from src.model_registry import MODEL_KEYS, MODEL_DISPLAY_NAMES


# ============================================================================
# CONSTANTS
# ============================================================================
DISEASE_CLASSES = ["Black_rot", "Esca", "Healthy", "Leaf_blight"]
REPORTS_DIR = Path("reports")
MODELS_DIR = Path("models")


# ============================================================================
# FUNCTIONS FROM PREVIOUS APP
# ============================================================================

def load_model_ranking():
    ranking_path = Path("reports/modelos/ranking_modelos.csv")
    best_path = Path("reports/modelos/mejor_modelo.txt")
    try:
        ranking_data = None
        best_model_name = None
        if ranking_path.exists():
            df = pd.read_csv(ranking_path)
            ranking_data = df.to_dict("records")
        if best_path.exists():
            with open(best_path, "r", encoding="utf-8") as f:
                best_model_name = f.read().strip()
        return ranking_data, best_model_name
    except Exception:
        return None, None


@st.cache_resource
def load_models() -> dict[str, dict]:
    resultados: dict[str, dict] = {}
    for modelo in MODEL_KEYS:
        try:
            cargar_modelo(modelo)
            resultados[modelo] = {"disponible": True, "error": None}
        except Exception as exc:
            resultados[modelo] = {"disponible": False, "error": str(exc)}
    return resultados


def check_pipeline_status():
    checks = {
        "eda": {
            "label_es": "EDA - Análisis exploratorio",
            "label_en": "EDA - Exploratory analysis",
            "label_pt": "EDA - Análise exploratória",
            "files": [Path("reports/eda/resumen_dataset.csv"), Path("reports/eda/distribucion_clases.png")],
        },
        "preprocessing": {
            "label_es": "Preprocesamiento y aumento",
            "label_en": "Preprocessing & augmentation",
            "label_pt": "Pré-processamento e aumento",
            "files": [Path("reports/preprocessing/ejemplos_aumento_datos.png")],
        },
        "crossval": {
            "label_es": "Validación cruzada (5-folds)",
            "label_en": "Cross-validation (5-fold)",
            "label_pt": "Validação cruzada (5-fold)",
            "files": [Path("reports/modelos/cross_validation/cross_validation_resultados.csv")],
        },
        "hyperparam": {
            "label_es": "Optimización de hiperparámetros",
            "label_en": "Hyperparameter optimization",
            "label_pt": "Otimização de hiperparâmetros",
            "files": [Path("reports/modelos/tuning/mejores_hiperparametros.csv")],
        },
        "statistical": {
            "label_es": "Validación estadística",
            "label_en": "Statistical validation",
            "label_pt": "Validação estatística",
            "files": [Path("reports/estadistica/mcnemar_resultados.csv")],
        },
        "model_selection": {
            "label_es": "Selección del mejor modelo",
            "label_en": "Best model selection",
            "label_pt": "Seleção do melhor modelo",
            "files": [Path("reports/modelos/ranking_modelos.csv")],
        },
    }
    lang = st.session_state.get("language", "es")
    results = {}
    for key, check in checks.items():
        done = all(f.exists() for f in check["files"])
        label = check.get(f"label_{lang}", check["label_es"])
        results[key] = {"done": done, "label": label}
    return results


def validar_cross_validation() -> bool:
    archivo = Path("reports/modelos/cross_validation/cross_validation_resultados.csv")
    if not archivo.is_file():
        return False
    try:
        df = pd.read_csv(archivo)
        columnas_requeridas = {"modelo", "accuracy_mean", "accuracy_std"}
        return not df.empty and columnas_requeridas.issubset(df.columns) and df["accuracy_mean"].notna().any()
    except Exception:
        return False


# ============================================================================
# INITIALIZATION
# ============================================================================

st.set_page_config(
    page_title="VineGuard AI",
    page_icon="🍇",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Session state
if "language" not in st.session_state:
    st.session_state.language = "es"
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user" not in st.session_state:
    st.session_state.user = None
if "page" not in st.session_state:
    st.session_state.page = "dashboard"
if "model_status" not in st.session_state:
    st.session_state.model_status = {}
if "models_loaded" not in st.session_state:
    st.session_state.models_loaded = False
if "predictions" not in st.session_state:
    st.session_state.predictions = None
if "ranking_data" not in st.session_state:
    ranking_data, best_model_name = load_model_ranking()
    st.session_state.ranking_data = ranking_data
    st.session_state.best_model_name = best_model_name

# Init database
try:
    init_database()
except Exception:
    pass

# ─── Render theme ──────────────────────────────────────────────────────────
render_theme()

# ─── Language selector (top, before login) ─────────────────────────────────
lang = st.session_state.language
col_lang1, col_lang2 = st.columns([3.5, 1.5])
with col_lang2:
    language_options = {
        "Español": "es",
        "English": "en",
        "Português": "pt",
    }
    selected_language = st.selectbox(
        "Language / Idioma",
        options=list(language_options.keys()),
        index=list(language_options.values()).index(lang),
        key="main_language_selector",
    )
    new_language = language_options[selected_language]
    if new_language != lang:
        st.session_state.language = new_language
        st.rerun()

st.markdown("---")


# ============================================================================
# AUTHENTICATION GATE
# ============================================================================

if not st.session_state.logged_in:
    render_login()
    st.stop()

# ============================================================================
# MAIN APP (authenticated)
# ============================================================================

render_sidebar()

user = st.session_state.user
role = user.get("role", "client") if user else "client"
page = st.session_state.get("page", "dashboard")

_t = lambda es, en, pt: {"es": es, "en": en, "pt": pt}.get(st.session_state.language, es)

# ─── Page routing ──────────────────────────────────────────────────────────

if page == "diagnosis":
    render_header(
        _t("Nuevo Diagnóstico", "New Diagnosis", "Novo Diagnóstico"),
        _t("Analiza una hoja de vid", "Analyze a vine leaf", "Analise uma folha de videira"),
    )
    diagnosis_view()
elif page == "history":
    render_header(
        _t("Historial", "History", "Histórico"),
        _t("Diagnósticos realizados", "Past diagnoses", "Diagnósticos realizados"),
    )
    history_view()
elif page == "models" and role == "admin":
    render_header(
        _t("Gestión de Modelos", "Model Management", "Gerenciamento de Modelos"),
        _t("Estado y métricas de los modelos", "Model status and metrics", "Status e métricas dos modelos"),
    )
    models_view()
elif page == "pipeline" and role == "admin":
    render_header(
        _t("Estado del Pipeline", "Pipeline Status", "Status do Pipeline"),
        _t("Progreso del flujo de experimentación", "Experimentation flow progress", "Progresso do fluxo de experimentação"),
    )
    pipeline_view()
elif page == "statistics" and role == "admin":
    render_header(
        _t("Estadísticas", "Statistics", "Estatísticas"),
        _t("Análisis estadístico de rendimiento", "Performance statistical analysis", "Análise estatística de desempenho"),
    )
    statistics_view()
elif page == "reports" and role == "admin":
    render_header(
        _t("Reportes", "Reports", "Relatórios"),
        _t("Visualiza y descarga reportes", "View and download reports", "Visualize e baixe relatórios"),
    )
    reports_view()
elif page == "info":
    render_header(
        _t("Información", "Information", "Informação"),
        _t("Acerca del sistema", "About the system", "Sobre o sistema"),
    )
    info_view()
else:
    if role == "admin":
        render_header(
            _t("Panel de Administración", "Admin Dashboard", "Painel de Administração"),
            _t("Resumen ejecutivo del sistema", "System executive summary", "Resumo executivo do sistema"),
        )
        admin_dashboard()
    else:
        render_header(
            _t("Inicio", "Home", "Início"),
            _t("Bienvenido a VineGuard AI", "Welcome to VineGuard AI", "Bem-vindo ao VineGuard AI"),
        )
        client_dashboard()


if __name__ == "__main__":
    pass
