"""Model comparison view — ranking by MCC, F1, Accuracy with charts."""

import streamlit as st
import pandas as pd
from pathlib import Path
from ui.components import section_header, empty_state, info_box, run_script_button, reload_ranking_callback


def _t(es: str, en: str, pt: str) -> str:
    lang = st.session_state.get("language", "es")
    return {"es": es, "en": en, "pt": pt}.get(lang, es)


def _fmt_metric(val) -> str:
    if val is None or val == "":
        return "N/A"
    try:
        return f"{float(val):.4f}"
    except (TypeError, ValueError):
        return str(val)


def render():
    lang = st.session_state.get("language", "es")
    section_header(
        _t("Comparación de Modelos", "Model Comparison", "Comparação de Modelos"),
        _t("Ranking completo ordenado por MCC, F1-macro y Accuracy", "Full ranking sorted by MCC, F1-macro and Accuracy", "Ranking completo ordenado por MCC, F1-macro e Acurácia"),
        "🏆",
    )

    col1, col2 = st.columns(2)
    with col1:
        run_script_button(
            "src/evaluacion_comparativa.py",
            _t("🏆 Comparar modelos", "🏆 Compare models", "🏆 Comparar modelos"),
            key="run_comparison",
            confirm_message=_t(
                "¿Ejecutar evaluación comparativa de todos los modelos?",
                "Run comparative evaluation of all models?",
                "Executar avaliação comparativa de todos os modelos?",
            ),
            reload_callback=reload_ranking_callback,
        )
    with col2:
        run_script_button(
            "src/seleccion_mejor_modelo.py",
            _t("⭐ Seleccionar mejor modelo", "⭐ Select best model", "⭐ Selecionar melhor modelo"),
            key="run_select_best",
            reload_callback=reload_ranking_callback,
        )

    ranking = st.session_state.get("ranking_data", []) or []
    if not ranking:
        empty_state("🏆", _t("Ranking no disponible", "Ranking not available", "Ranking indisponível"),
                     _t("Ejecuta src/seleccion_mejor_modelo.py para generar el ranking.", "Run src/seleccion_mejor_modelo.py to generate the ranking.", "Execute src/seleccion_mejor_modelo.py para gerar o ranking."))
        return

    df = pd.DataFrame(ranking)
    sort_cols = [c for c in ["mcc", "f1_score", "accuracy"] if c in df.columns]

    st.markdown(f"### {_t('Ranking de Modelos', 'Model Ranking', 'Ranking de Modelos')}")
    if sort_cols:
        df_sorted = df.sort_values(by=sort_cols, ascending=False).reset_index(drop=True)
        df_sorted.index = df_sorted.index + 1
        df_sorted.index.name = "#"

        display_cols = [c for c in ["modelo", "accuracy", "f1_score", "mcc", "precision", "recall"] if c in df_sorted.columns]
        if display_cols:
            st.dataframe(df_sorted[display_cols], use_container_width=True)

        if not df_sorted.empty:
            winner = df_sorted.iloc[0]
            st.success(
                f"🥇 **{_t('Primer lugar', 'First place', 'Primeiro lugar')}:** "
                f"{winner.get('modelo', '—')}  "
                f"| Accuracy: {_fmt_metric(winner.get('accuracy'))}"
                f" | F1: {_fmt_metric(winner.get('f1_score'))}"
                f" | MCC: {_fmt_metric(winner.get('mcc'))}"
            )
    else:
        st.dataframe(df, use_container_width=True, hide_index=True)

    st.markdown("---")

    comp_dir = Path("reports/modelos/comparativos")
    if comp_dir.exists():
        csv_files = sorted(comp_dir.glob("*.csv"))
        for csv_f in csv_files:
            try:
                df_comp = pd.read_csv(csv_f)
                if not df_comp.empty:
                    with st.expander(f"**{csv_f.stem.replace('_', ' ').title()}**"):
                        st.dataframe(df_comp, use_container_width=True, hide_index=True)
            except Exception:
                pass

        png_files = sorted(comp_dir.glob("*.png"))
        if png_files:
            st.markdown(f"### {_t('Gráficos comparativos', 'Comparison charts', 'Gráficos comparativos')}")
            cols = st.columns(2)
            for i, img_path in enumerate(png_files):
                with cols[i % 2]:
                    st.image(str(img_path), use_column_width=True, caption=img_path.stem)
