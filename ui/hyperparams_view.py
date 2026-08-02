"""Hyperparameter tuning view — best parameters per model."""

import streamlit as st
import pandas as pd
from pathlib import Path
from ui.components import empty_state, info_box, run_script_button


TUNING_DIR = Path("reports/modelos/tuning")


def _t(es: str, en: str, pt: str) -> str:
    lang = st.session_state.get("language", "es")
    return {"es": es, "en": en, "pt": pt}.get(lang, es)


def render():
    run_script_button(
        "src/optimizacion_hiperparametros.py",
        _t("⚙️ Ejecutar tuning", "⚙️ Run tuning", "⚙️ Executar tuning"),
        key="run_tuning",
        confirm_message=_t(
            "¿Ejecutar optimización de hiperparámetros en todos los modelos?",
            "Run hyperparameter optimization on all models?",
            "Executar otimização de hiperparâmetros em todos os modelos?",
        ),
    )

    if not TUNING_DIR.exists():
        empty_state("⚙️", _t("Sin resultados de tuning", "No tuning results", "Sem resultados de tuning"),
                     _t("Ejecuta src/optimizacion_hiperparametros.py para generar los resultados.", "Run src/optimizacion_hiperparametros.py to generate results.", "Execute src/optimizacion_hiperparametros.py para gerar resultados."))
        return

    csv_files = sorted(TUNING_DIR.glob("*.csv"))
    pkl_files = sorted(TUNING_DIR.glob("*.pkl"))

    if csv_files:
        for csv_f in csv_files:
            try:
                df = pd.read_csv(csv_f)
                if not df.empty:
                    with st.expander(f"**{csv_f.stem.replace('_', ' ').title()}**", expanded=True):
                        st.dataframe(df, use_container_width=True, hide_index=True)
            except Exception as e:
                info_box(f"Error reading {csv_f.name}: {e}", "error")

    if pkl_files:
        st.markdown(f"### {_t('Artefactos guardados', 'Saved artifacts', 'Artefatos salvos')}")
        for pkl_f in pkl_files:
            size = pkl_f.stat().st_size / 1024
            st.markdown(f"- `{pkl_f.name}`  ({size:.1f} KB)")

    tuning_img = TUNING_DIR / "tuning_comparison.png"
    if tuning_img.exists():
        st.markdown(f"### {_t('Gráfico comparativo', 'Comparison chart', 'Gráfico comparativo')}")
        st.image(str(tuning_img), use_column_width=True)

    if not csv_files and not pkl_files and not tuning_img.exists():
        empty_state("⚙️", _t("Carpeta vacía", "Empty folder", "Pasta vazia"),
                     _t("La carpeta de tuning no contiene archivos.", "The tuning folder contains no files.", "A pasta de tuning não contém arquivos."))
