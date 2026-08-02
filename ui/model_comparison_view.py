"""Model comparison view — ranking by MCC, F1-macro, Accuracy with charts."""

import streamlit as st
import pandas as pd
from pathlib import Path
from ui.components import empty_state, info_box, run_script_button

COMP_DIR = Path("reports/modelos/comparativos")
REPORTS_DIR = Path("reports/modelos")


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


def _load_comparison() -> pd.DataFrame | None:
    p = COMP_DIR / "comparacion_general_modelos.csv"
    if not p.exists():
        return None
    try:
        return pd.read_csv(p)
    except Exception:
        return None


def _load_f1_por_clase() -> pd.DataFrame | None:
    p = COMP_DIR / "comparacion_f1_por_clase.csv"
    if not p.exists():
        return None
    try:
        return pd.read_csv(p)
    except Exception:
        return None


def render():
    run_script_button(
        "src/evaluacion_comparativa.py",
        _t("🏆 Actualizar comparación", "🏆 Update comparison", "🏆 Atualizar comparação"),
        key="run_comparison",
        confirm_message=_t(
            "¿Ejecutar evaluación comparativa de todos los modelos?",
            "Run comparative evaluation of all models?",
            "Executar avaliação comparativa de todos os modelos?",
        ),
        reload_callback=_reload_ranking,
    )

    df = _load_comparison()
    if df is None or df.empty:
        empty_state(
            "🏆",
            _t("Ranking no disponible", "Ranking not available", "Ranking indisponível"),
            _t("Ejecuta la comparación de modelos para generar el ranking.",
              "Run model comparison to generate the ranking.",
              "Execute a comparação de modelos para gerar o ranking."),
        )
        return

    # ── Orden consistente con el CSV: MCC → F1 → Accuracy ──────────
    sort_cols = [c for c in ["mcc", "f1_score", "accuracy"] if c in df.columns]
    if sort_cols:
        df = df.sort_values(by=sort_cols, ascending=False).reset_index(drop=True)

    # ── Tabla principal ─────────────────────────────────────────────
    st.markdown(f"### {_t('Ranking de Modelos', 'Model Ranking', 'Ranking de Modelos')}")

    display_map = {
        "modelo": "Modelo",
        "accuracy": "Accuracy",
        "balanced_accuracy": "Balanced Accuracy",
        "f1_score": "F1-macro",
        "mcc": "MCC",
        "precision": "Precisión macro",
        "recall": "Recall macro",
    }
    available = [c for c in display_map if c in df.columns]
    mostrar = df[available].copy()
    mostrar.columns = [display_map[c] for c in available]
    for col in mostrar.columns:
        if col != "Modelo":
            mostrar[col] = mostrar[col].apply(_fmt_metric)

    st.dataframe(mostrar, use_container_width=True, hide_index=True)

    # ── Ganador ─────────────────────────────────────────────────────
    if not df.empty:
        winner = df.iloc[0]
        info_box(
            _t(
                f"🥇 **Primer lugar:** {winner.get('modelo', '—')}  "
                f"| MCC: {_fmt_metric(winner.get('mcc'))}"
                f" | F1-macro: {_fmt_metric(winner.get('f1_score'))}"
                f" | Accuracy: {_fmt_metric(winner.get('accuracy'))}",
                f"🥇 **First place:** {winner.get('modelo', '—')}  "
                f"| MCC: {_fmt_metric(winner.get('mcc'))}"
                f" | F1-macro: {_fmt_metric(winner.get('f1_score'))}"
                f" | Accuracy: {_fmt_metric(winner.get('accuracy'))}",
                f"🥇 **Primeiro lugar:** {winner.get('modelo', '—')}  "
                f"| MCC: {_fmt_metric(winner.get('mcc'))}"
                f" | F1-macro: {_fmt_metric(winner.get('f1_score'))}"
                f" | Accuracy: {_fmt_metric(winner.get('accuracy'))}",
            ),
            type_="success",
        )
        info_box(
            _t(
                "El ranking prioriza MCC, seguido de F1-macro y Accuracy.",
                "Ranking prioritizes MCC, followed by F1-macro and Accuracy.",
                "O ranking prioriza MCC, seguido de F1-macro e Acurácia.",
            ),
            type_="info",
        )

    st.markdown("---")

    # ── F1 por clase ────────────────────────────────────────────────
    df_f1 = _load_f1_por_clase()
    if df_f1 is not None and not df_f1.empty:
        rename_f1 = {"modelo": "Modelo"}
        for c in df_f1.columns:
            if c not in rename_f1 and c != "f1_macro_calculado":
                rename_f1[c] = c
        rename_f1["f1_macro_calculado"] = "F1-macro calculado"
        mostrar_f1 = df_f1.rename(columns=rename_f1).copy()
        if "F1-macro calculado" in mostrar_f1.columns:
            mostrar_f1["F1-macro calculado"] = mostrar_f1["F1-macro calculado"].apply(_fmt_metric)

        # Validar consistencia con la tabla principal
        f1_check = {}
        inconsistente = False
        if "F1-macro calculado" in mostrar_f1.columns:
            for _, r in mostrar_f1.iterrows():
                f1_check[str(r.get("Modelo", ""))] = r.get("F1-macro calculado")
        if df is not None and not df.empty:
            inconsistente = False
            for _, r in df.iterrows():
                modelo = str(r.get("modelo", ""))
                general_f1 = r.get("f1_score")
                calc_f1 = f1_check.get(modelo)
                if general_f1 is not None and calc_f1 is not None:
                    try:
                        if abs(float(general_f1) - float(calc_f1)) > 0.01:
                            inconsistente = True
                            break
                    except (TypeError, ValueError):
                        inconsistente = True
                        break

        if inconsistente:
            info_box(
                _t(
                    "⚠️ Los valores de F1 por clase son inconsistentes con las métricas generales. "
                    "Regenera la evaluación comparativa.",
                    "⚠️ F1 per class values are inconsistent with general metrics. "
                    "Regenerate the comparative evaluation.",
                    "⚠️ Os valores de F1 por classe são inconsistentes com as métricas gerais. "
                    "Regenere a avaliação comparativa.",
                ),
                type_="error",
            )
        else:
            with st.expander(
                _t("📊 F1 por clase", "📊 F1 per class", "📊 F1 por classe"),
                expanded=False,
            ):
                st.dataframe(mostrar_f1, use_container_width=True, hide_index=True)
                info_box(
                    _t(
                        "El F1 por clase muestra el equilibrio entre precisión y recall para cada "
                        "enfermedad. El F1-macro calculado corresponde al promedio simple de las "
                        "cuatro clases.",
                        "Per-class F1 shows the balance between precision and recall for each "
                        "disease. The calculated F1-macro is the simple average of the four classes.",
                        "O F1 por classe mostra o equilíbrio entre precisão e recall para cada "
                        "doença. O F1-macro calculado corresponde à média simples das quatro classes.",
                    ),
                    type_="info",
                )
    else:
        pass  # No se encontró archivo, no mostrar nada

    # ── Gráficos comparativos ───────────────────────────────────────
    png_files = sorted(COMP_DIR.glob("*.png"))
    if png_files:
        st.markdown(f"### {_t('Gráficos comparativos', 'Comparison charts', 'Gráficos comparativos')}")
        cols = st.columns(2)
        for i, img_path in enumerate(png_files):
            with cols[i % 2]:
                st.image(str(img_path), use_column_width=True, caption=img_path.stem)


def _reload_ranking():
    ranking_path = REPORTS_DIR / "ranking_modelos.csv"
    best_path = REPORTS_DIR / "mejor_modelo.txt"
    try:
        if ranking_path.exists():
            df = pd.read_csv(ranking_path)
            st.session_state.ranking_data = df.to_dict("records")
        if best_path.exists():
            with open(best_path, encoding="utf-8") as f:
                st.session_state.best_model_name = f.read().strip()
    except Exception:
        pass
