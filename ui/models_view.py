"""Models management view for administrators — native Streamlit, sin HTML custom."""

import streamlit as st
import pandas as pd
from pathlib import Path
from ui.components import section_header, status_badge, empty_state, info_box


MODEL_INFO = {
    "M1": {"name": "M1 - SVM",           "type": "Clásico",  "file": "svm_model.pkl"},
    "M2": {"name": "M2 - Random Forest",  "type": "Clásico",  "file": "random_forest_model.pkl"},
    "M3": {"name": "M3 - KNN",            "type": "Clásico",  "file": "knn_model.pkl"},
    "H1": {"name": "H1 - CNN + SVM",      "type": "Híbrido",  "file": "cnn_svm_model.pkl"},
    "H2": {"name": "H2 - Transfer + RF",  "type": "Híbrido",  "file": "transfer_random_forest_model.pkl"},
}


def _fmt_metric(val) -> str:
    """Formatea un valor de métrica de forma segura."""
    if val is None or val == "":
        return "N/A"
    try:
        return f"{float(val):.4f}"
    except (TypeError, ValueError):
        return str(val)


def render():
    lang = st.session_state.get("language", "es")

    section_header(
        "Gestión de Modelos",
        "Estado y métricas de todos los modelos del sistema",
        "🧠",
    )

    best_model = st.session_state.get("best_model_name", "") or ""
    best_clean = best_model.split(":")[1].strip() if ":" in best_model else best_model

    model_status = st.session_state.get("model_status", {}) or {}
    ranking    = st.session_state.get("ranking_data", []) or []

    # ── Tarjetas de modelos: 3 columnas, componentes nativos ────────────────
    cols = st.columns(3)
    for i, (mk, info) in enumerate(MODEL_INFO.items()):
        with cols[i % 3]:
            available = model_status.get(mk, {}).get("disponible", False)
            is_best   = bool(best_clean) and (best_clean in info["name"] or best_clean == mk)

            # Buscar métricas desde ranking
            metrics: dict = {}
            for r in ranking:
                if r.get("modelo") and mk in r.get("modelo", ""):
                    for k in ["accuracy", "f1_score", "mcc"]:
                        metrics[k] = r.get(k, None)
                    break

            # --- Cabecera del modelo ---
            header_text = f"{'⭐ ' if is_best else ''}{info['name']}"
            st.markdown(f"**{header_text}**")
            st.caption(f"{info['type']} · {status_badge('loaded' if available else 'not_loaded', 'Disponible' if available else 'No disponible')}")

            # --- Métricas ---
            m_col1, m_col2, m_col3 = st.columns(3)
            with m_col1:
                st.metric("Accuracy", _fmt_metric(metrics.get("accuracy")))
            with m_col2:
                st.metric("F1-macro", _fmt_metric(metrics.get("f1_score")))
            with m_col3:
                st.metric("MCC", _fmt_metric(metrics.get("mcc")))

            # --- Archivo del modelo ---
            if available:
                st.caption(f"📄 {info['file']}")
            else:
                st.caption("📭 No cargado")

            st.divider()

    # ── Ranking completo ────────────────────────────────────────────────────
    if ranking:
        st.markdown("### Ranking Completo de Modelos")
        df = pd.DataFrame(ranking)
        cols_show = [c for c in ["ranking", "modelo", "accuracy", "f1_score", "mcc", "precision", "recall"]
                     if c in df.columns]
        if cols_show:
            st.dataframe(df[cols_show], use_container_width=True, hide_index=True)
    else:
        empty_state("📊", "Ranking no disponible",
                    "Ejecuta la selección del mejor modelo para ver el ranking.")

    # ── Cargar modelos ──────────────────────────────────────────────────────
    st.markdown("### Cargar Modelos")
    load_label = (
        "Cargar modelos ahora" if lang == "es"
        else "Load models now" if lang == "en"
        else "Carregar modelos agora"
    )
    if st.button(load_label, type="primary", key="load_models_btn"):
        spinner_msg = (
            "Cargando modelos..." if lang == "es"
            else "Loading models..." if lang == "en"
            else "Carregando modelos..."
        )
        with st.spinner(spinner_msg):
            from predecir_imagen import cargar_modelo as _cargar_modelo
            estado: dict = {}
            for mk in ["M1", "M2", "M3", "H1", "H2"]:
                try:
                    _cargar_modelo(mk)
                    estado[mk] = {"disponible": True, "error": None}
                except Exception as exc:
                    estado[mk] = {"disponible": False, "error": str(exc)}
            st.session_state.model_status = estado
            st.session_state.models_loaded = any(e["disponible"] for e in estado.values())
            if st.session_state.models_loaded:
                info_box(
                    "Modelos cargados exitosamente." if lang == "es"
                    else "Models loaded successfully." if lang == "en"
                    else "Modelos carregados com sucesso.",
                    "success",
                )
            else:
                info_box(
                    "No se pudieron cargar los modelos." if lang == "es"
                    else "Could not load models." if lang == "en"
                    else "Não foi possível carregar os modelos.",
                    "error",
                )
            st.rerun()
