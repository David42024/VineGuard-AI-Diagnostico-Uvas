"""Statistics and validation view for administrators."""

import streamlit as st
import pandas as pd
from pathlib import Path
from ui.components import section_header, empty_state, info_box


def render():
    lang = st.session_state.get("language", "es")
    section_header(
        "Estadísticas y Validación",
        "Análisis estadístico de rendimiento de modelos",
        "📊",
    )

    _render_model_comparison()
    _render_confusion_matrices()
    _render_roc_curves()
    _render_cross_validation()
    _render_statistical_tests()


def _render_model_comparison():
    st.markdown("### Comparación de Métricas")
    ranking = st.session_state.get("ranking_data", []) or []
    if ranking:
        df = pd.DataFrame(ranking)
        display_cols = [c for c in ["modelo", "accuracy", "f1_score", "mcc", "precision", "recall"] if c in df.columns]
        if display_cols:
            st.dataframe(df[display_cols], use_container_width=True, hide_index=True)

        best = st.session_state.get("best_model_name", "") or ""
        if best:
            st.markdown(f"**Mejor modelo:** {best}")
    else:
        empty_state("📊", "Métricas no disponibles", "Ejecuta el entrenamiento y la selección del mejor modelo para ver métricas comparativas.")


def _render_confusion_matrices():
    cm_dir = Path("reports/modelos")
    cm_files = sorted(cm_dir.glob("confusion_*.png"))
    if cm_files:
        st.markdown("### Matrices de Confusión")
        cols = st.columns(min(len(cm_files), 5))
        for i, f in enumerate(cm_files):
            with cols[i % len(cols)]:
                st.image(str(f), use_column_width=True, caption=f.stem.replace("confusion_", "").replace("_", " ").title())
    else:
        info_box("Matrices de confusión no disponibles. Entrena los modelos para generarlas.", "info")


def _render_roc_curves():
    roc_dir = Path("reports/modelos")
    roc_files = sorted(roc_dir.glob("roc_*.png"))
    if roc_files:
        st.markdown("### Curvas ROC")
        cols = st.columns(min(len(roc_files), 5))
        for i, f in enumerate(roc_files):
            with cols[i % len(cols)]:
                st.image(str(f), use_column_width=True, caption=f.stem.replace("roc_", "").replace("_", " ").title())
    else:
        info_box("Curvas ROC no disponibles. Entrena los modelos para generarlas.", "info")


def _render_cross_validation():
    cv_path = Path("reports/modelos/cross_validation/cross_validation_resultados.csv")
    if cv_path.exists():
        st.markdown("### Validación Cruzada (5-folds)")
        df_cv = pd.read_csv(cv_path)
        st.dataframe(df_cv, use_container_width=True, hide_index=True)

        cv_img = Path("reports/modelos/cross_validation/cross_validation_comparacion.png")
        if cv_img.exists():
            st.image(str(cv_img), use_column_width=True)
    else:
        info_box("Validación cruzada no disponible. Ejecuta cross_validation_modelos.py.", "info")


def _render_statistical_tests():
    stat_dir = Path("reports/estadistica")
    if not stat_dir.exists():
        empty_state("📊", "Validación estadística no disponible", "Ejecuta validacion_estadistica_modelos.py.")
        return

    st.markdown("### Validación Estadística")

    mcnemar_path = stat_dir / "mcnemar_resultados.csv"
    if mcnemar_path.exists():
        st.markdown("#### Prueba de McNemar")
        df_mc = pd.read_csv(mcnemar_path)
        st.dataframe(df_mc, use_container_width=True, hide_index=True)

    cochran_path = stat_dir / "cochran_q_resultado.csv"
    if cochran_path.exists():
        st.markdown("#### Prueba de Cochran Q")
        df_cq = pd.read_csv(cochran_path)
        st.dataframe(df_cq, use_container_width=True, hide_index=True)

    bootstrap_path = stat_dir / "intervalos_confianza_bootstrap.csv"
    if bootstrap_path.exists():
        st.markdown("#### Intervalos de Confianza (Bootstrap)")
        df_bs = pd.read_csv(bootstrap_path)
        st.dataframe(df_bs, use_container_width=True, hide_index=True)

    effect_path = stat_dir / "tamano_efecto.csv"
    if effect_path.exists():
        st.markdown("#### Tamaño del Efecto")
        df_ef = pd.read_csv(effect_path)
        st.dataframe(df_ef, use_container_width=True, hide_index=True)

    if not any(p.exists() for p in [mcnemar_path, cochran_path, bootstrap_path, effect_path]):
        empty_state("📊", "Reportes estadísticos no disponibles", "Ejecuta validacion_estadistica_modelos.py para generar los reportes.")
