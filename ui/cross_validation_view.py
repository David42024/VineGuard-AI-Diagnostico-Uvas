"""Cross-validation view — fold results, mean, std, and charts."""

import streamlit as st
import pandas as pd
from pathlib import Path
from ui.components import empty_state, info_box, run_script_button


CV_DIR = Path("reports/modelos/cross_validation")


def _t(es: str, en: str, pt: str) -> str:
    lang = st.session_state.get("language", "es")
    return {"es": es, "en": en, "pt": pt}.get(lang, es)


def render():
    run_script_button(
        "src/cross_validation_modelos.py",
        _t("📐 Ejecutar validación cruzada", "📐 Run cross-validation", "📐 Executar validação cruzada"),
        key="run_crossval",
        confirm_message=_t(
            "¿Ejecutar validación cruzada en todos los modelos?",
            "Run cross-validation on all models?",
            "Executar validação cruzada em todos os modelos?",
        ),
    )

    is_running = st.session_state.get("_running_run_crossval", False)

    if not CV_DIR.exists():
        if is_running:
            st.info(_t("⏳ La validación cruzada está en ejecución. Los resultados aparecerán al finalizar.", "⏳ Cross-validation is running. Results will appear when finished.", "⏳ A validação cruzada está em execução. Os resultados aparecerão quando concluída."))
        else:
            empty_state("📐", _t("Validación cruzada no disponible", "Cross-validation not available", "Validação cruzada indisponível"),
                        _t("Ejecuta src/cross_validation_modelos.py para generar los resultados.", "Run src/cross_validation_modelos.py to generate results.", "Execute src/cross_validation_modelos.py para gerar resultados."))
        return

    cv_csv = CV_DIR / "cross_validation_resultados.csv"
    if cv_csv.exists():
        try:
            df = pd.read_csv(cv_csv)
            st.markdown(f"### {_t('Resultados por modelo', 'Results per model', 'Resultados por modelo')}")
            st.dataframe(df, use_container_width=True, hide_index=True)

            numeric_cols = df.select_dtypes(include="number").columns
            if not df.empty and len(numeric_cols) > 0:
                st.markdown(f"### {_t('Resumen', 'Summary', 'Resumo')}")
                summary = df[numeric_cols].agg(["mean", "std"]).round(4)
                st.dataframe(summary, use_container_width=True)
        except Exception as e:
            info_box(f"{_t('Error al leer', 'Error reading', 'Erro ao ler')}: {e}", "error")
    else:
        if is_running:
            st.info(_t("⏳ Procesando...", "⏳ Processing...", "⏳ Processando..."))
        else:
            empty_state("📐", _t("Sin resultados", "No results", "Sem resultados"),
                        _t("No se encontró el archivo de resultados de validación cruzada.", "Cross-validation results file not found.", "Arquivo de resultados de validação cruzada não encontrado."))

    for graf_name, graf_title in [
        ("cross_validation_accuracy.png", _t("Accuracy", "Accuracy", "Acurácia")),
        ("cross_validation_f1_macro.png", _t("F1-macro", "F1-macro", "F1-macro")),
        ("cross_validation_mcc.png", _t("MCC", "MCC", "MCC")),
    ]:
        graf_path = CV_DIR / graf_name
        if graf_path.exists():
            st.markdown(f"### {graf_title}")
            st.image(str(graf_path), use_column_width=True)

    extra_csvs = sorted(CV_DIR.glob("*.csv"))
    extra_csvs = [f for f in extra_csvs if f.name != "cross_validation_resultados.csv"]
    if extra_csvs:
        st.markdown(f"### {_t('Archivos adicionales', 'Additional files', 'Arquivos adicionais')}")
        for f in extra_csvs:
            try:
                df = pd.read_csv(f)
                with st.expander(f.stem):
                    st.dataframe(df, use_container_width=True, hide_index=True)
            except Exception:
                pass
