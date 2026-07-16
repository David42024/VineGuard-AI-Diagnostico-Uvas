"""Statistical tests view — McNemar, Cochran Q, Bootstrap, effect size."""

import streamlit as st
import pandas as pd
from pathlib import Path
from ui.components import section_header, empty_state, info_box, run_script_button


STAT_DIR = Path("reports/estadistica")


def _t(es: str, en: str, pt: str) -> str:
    lang = st.session_state.get("language", "es")
    return {"es": es, "en": en, "pt": pt}.get(lang, es)


def _read_csv(rel_path: str) -> pd.DataFrame | None:
    p = STAT_DIR / rel_path
    if not p.exists():
        return None
    try:
        return pd.read_csv(p)
    except Exception:
        return None


def render():
    lang = st.session_state.get("language", "es")
    section_header(
        _t("Pruebas Estadísticas", "Statistical Tests", "Testes Estatísticos"),
        _t("Validación estadística del rendimiento de los modelos", "Statistical validation of model performance", "Validação estatística do desempenho dos modelos"),
        "📈",
    )

    run_script_button(
        "src/validacion_estadistica_modelos.py",
        _t("📈 Ejecutar pruebas estadísticas", "📈 Run statistical tests", "📈 Executar testes estatísticos"),
        key="run_stats",
        confirm_message=_t(
            "¿Ejecutar todas las pruebas estadísticas (McNemar, Cochran Q, Bootstrap, etc.)?",
            "Run all statistical tests (McNemar, Cochran Q, Bootstrap, etc.)?",
            "Executar todos os testes estatísticos (McNemar, Cochran Q, Bootstrap, etc.)?",
        ),
    )

    if not STAT_DIR.exists():
        empty_state("📈", _t("Pruebas estadísticas no disponibles", "Statistical tests not available", "Testes estatísticos indisponíveis"),
                     _t("Ejecuta src/validacion_estadistica_modelos.py para generar los reportes.", "Run src/validacion_estadistica_modelos.py to generate reports.", "Execute src/validacion_estadistica_modelos.py para gerar relatórios."))
        return

    tests = []

    df_mc = _read_csv("mcnemar_resultados.csv")
    if df_mc is not None:
        tests.append(("McNemar", df_mc, "Prueba de McNemar — comparación por pares entre modelos"))

    df_holm = _read_csv("mcnemar_holm_posthoc.csv")
    if df_holm is not None:
        tests.append(("McNemar + Holm", df_holm, "Corrección de Holm para comparaciones múltiples"))

    df_cq = _read_csv("cochran_q_resultado.csv")
    if df_cq is not None:
        tests.append(("Cochran Q", df_cq, "Prueba de Cochran Q — comparación global de modelos"))

    df_bs = _read_csv("intervalos_confianza_bootstrap.csv")
    if df_bs is not None:
        tests.append(("Bootstrap", df_bs, "Intervalos de confianza Bootstrap estratificado"))

    df_ef = _read_csv("tamano_efecto.csv")
    if df_ef is not None:
        tests.append(("Tamaño del Efecto", df_ef, "Magnitud de las diferencias entre modelos"))

    df_dm = _read_csv("diebold_mariano_complementario.csv")
    if df_dm is not None:
        tests.append(("Diebold-Mariano", df_dm, "Prueba complementaria de Diebold-Mariano"))

    if tests:
        tab_labels = [t[0] for t in tests]
        tabs = st.tabs(tab_labels)
        for tab, (name, df, desc) in zip(tabs, tests):
            with tab:
                st.markdown(f"*{desc}*")
                st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        empty_state("📈", _t("Reportes no encontrados", "Reports not found", "Relatórios não encontrados"),
                     _t("No hay archivos CSV en reports/estadistica/.", "No CSV files in reports/estadistica/.", "Nenhum arquivo CSV em reports/estadistica/."))
