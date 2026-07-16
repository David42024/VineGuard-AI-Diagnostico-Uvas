"""
VineGuard AI Lab - Laboratorio técnico de Machine Learning
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

# --- UI Modules ---
from ui.theme import render_theme
from ui.auth import render_login, init_auth
from ui.layout import render_sidebar, render_header

from ui.pipeline_view import render as pipeline_view
from ui.dataset_eda_view import render as dataset_eda_view
from ui.preprocessing_view import render as preprocessing_view
from ui.training_view import render as training_view
from ui.cross_validation_view import render as cross_validation_view
from ui.hyperparams_view import render as hyperparams_view
from ui.statistical_tests_view import render as statistical_tests_view
from ui.model_comparison_view import render as model_comparison_view
from ui.best_model_view import render as best_model_view
from ui.reports_view import render as reports_view

# --- Database ---
from database.repository import init_database

# --- Shared prediction ---
from predecir_imagen import cargar_modelo
from src.model_registry import MODEL_KEYS, MODEL_DISPLAY_NAMES


# ============================================================================
# CONSTANTS
# ============================================================================
DISEASE_CLASSES = ["Black_rot", "Esca", "Healthy", "Leaf_blight"]
REPORTS_DIR = Path("reports")
MODELS_DIR = Path("models")


# ============================================================================
# FUNCTIONS
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


# ============================================================================
# INITIALIZATION
# ============================================================================

st.set_page_config(
    page_title="VineGuard AI Lab",
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
    st.session_state.page = "pipeline"
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

# --- Render theme ---
render_theme()

# --- Language selector (top, before login) ---
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
page = st.session_state.get("page", "pipeline")

_t = lambda es, en, pt: {"es": es, "en": en, "pt": pt}.get(st.session_state.language, es)

# --- Page routing ---

PAGES = {
    "pipeline": {
        "title_es": "Resumen del Pipeline",
        "title_en": "Pipeline Summary",
        "title_pt": "Resumo do Pipeline",
        "sub_es": "Estado detallado de cada etapa del flujo de Machine Learning",
        "sub_en": "Detailed status of each ML flow stage",
        "sub_pt": "Status detalhado de cada etapa do fluxo de ML",
        "view": pipeline_view,
    },
    "dataset_eda": {
        "title_es": "Dataset y EDA",
        "title_en": "Dataset & EDA",
        "title_pt": "Dataset e EDA",
        "sub_es": "Análisis exploratorio del dataset de hojas de vid",
        "sub_en": "Exploratory analysis of the vine leaf dataset",
        "sub_pt": "Análise exploratória do dataset de folhas de videira",
        "view": dataset_eda_view,
    },
    "preprocessing": {
        "title_es": "Preprocesamiento",
        "title_en": "Preprocessing",
        "title_pt": "Pré-processamento",
        "sub_es": "Configuración y ejemplos visuales del aumento de datos",
        "sub_en": "Configuration and visual examples of data augmentation",
        "sub_pt": "Configuração e exemplos visuais do aumento de dados",
        "view": preprocessing_view,
    },
    "training": {
        "title_es": "Entrenamiento",
        "title_en": "Training",
        "title_pt": "Treinamento",
        "sub_es": "Estado, métricas y artefactos de los 5 modelos",
        "sub_en": "Status, metrics and artifacts of the 5 models",
        "sub_pt": "Status, métricas e artefatos dos 5 modelos",
        "view": training_view,
    },
    "crossval": {
        "title_es": "Validación Cruzada",
        "title_en": "Cross-Validation",
        "title_pt": "Validação Cruzada",
        "sub_es": "Resultados por fold, media y desviación estándar",
        "sub_en": "Per-fold results, mean and standard deviation",
        "sub_pt": "Resultados por fold, média e desvio padrão",
        "view": cross_validation_view,
    },
    "hyperparams": {
        "title_es": "Hiperparámetros",
        "title_en": "Hyperparameters",
        "title_pt": "Hiperparâmetros",
        "sub_es": "Mejores parámetros encontrados por modelo",
        "sub_en": "Best parameters found per model",
        "sub_pt": "Melhores parâmetros encontrados por modelo",
        "view": hyperparams_view,
    },
    "stats_tests": {
        "title_es": "Pruebas Estadísticas",
        "title_en": "Statistical Tests",
        "title_pt": "Testes Estatísticos",
        "sub_es": "Validación estadística del rendimiento de los modelos",
        "sub_en": "Statistical validation of model performance",
        "sub_pt": "Validação estatística do desempenho dos modelos",
        "view": statistical_tests_view,
    },
    "comparison": {
        "title_es": "Comparación de Modelos",
        "title_en": "Model Comparison",
        "title_pt": "Comparação de Modelos",
        "sub_es": "Ranking completo ordenado por MCC, F1-macro y Accuracy",
        "sub_en": "Full ranking sorted by MCC, F1-macro and Accuracy",
        "sub_pt": "Ranking completo ordenado por MCC, F1-macro e Acurácia",
        "view": model_comparison_view,
    },
    "best_model": {
        "title_es": "Mejor Modelo",
        "title_en": "Best Model",
        "title_pt": "Melhor Modelo",
        "sub_es": "Modelo seleccionado como óptimo para diagnóstico",
        "sub_en": "Model selected as optimal for diagnosis",
        "sub_pt": "Modelo selecionado como ótimo para diagnóstico",
        "view": best_model_view,
    },
    "reports": {
        "title_es": "Reportes",
        "title_en": "Reports",
        "title_pt": "Relatórios",
        "sub_es": "Visualiza y descarga los reportes generados",
        "sub_en": "View and download generated reports",
        "sub_pt": "Visualize e baixe os relatórios gerados",
        "view": reports_view,
    },
}

page_info = PAGES.get(page)
if page_info:
    render_header(
        _t(page_info["title_es"], page_info["title_en"], page_info["title_pt"]),
        _t(page_info["sub_es"], page_info["sub_en"], page_info["sub_pt"]),
    )
    page_info["view"]()
else:
    st.session_state.page = "pipeline"
    st.rerun()


if __name__ == "__main__":
    pass
