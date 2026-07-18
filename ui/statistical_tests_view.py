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

    if tests:
        tab_labels = [t[0] for t in tests]
        tabs = st.tabs(tab_labels)
        interpretaciones = {
            "McNemar": _t(
                "La prueba de McNemar compara si dos modelos tienen diferencias significativas en sus predicciones. "
                "Un **valor p < 0.05** indica que los modelos se comportan de manera distinta (significativo). "
                "Si el valor p es alto (≥ 0.05), no hay evidencia suficiente para decir que los modelos difieren.",
                "McNemar's test compares whether two models have significant differences in their predictions. "
                "A **p-value < 0.05** indicates the models behave differently (significant). "
                "If the p-value is high (≥ 0.05), there is insufficient evidence to say the models differ.",
                "O teste de McNemar compara se dois modelos têm diferenças significativas nas suas previsões. "
                "Um **valor p < 0.05** indica que os modelos se comportam de forma diferente (significativo). "
                "Se o valor p for alto (≥ 0.05), não há evidência suficiente para dizer que os modelos diferem.",
            ),
            "McNemar + Holm": _t(
                "La corrección de Holm ajusta los valores p al hacer múltiples comparaciones, "
                "reduciendo la probabilidad de falsos positivos. Un resultado **significativo** después "
                "de la corrección Holm indica una diferencia robusta entre los modelos.",
                "Holm's correction adjusts p-values when making multiple comparisons, "
                "reducing the probability of false positives. A **significant** result after "
                "Holm correction indicates a robust difference between models.",
                "A correção de Holm ajusta os valores p ao fazer múltiplas comparações, "
                "reduzindo a probabilidade de falsos positivos. Um resultado **significativo** após "
                "a correção de Holm indica uma diferença robusta entre os modelos.",
            ),
            "Cochran Q": _t(
                "La prueba de Cochran Q evalúa si **todos los modelos tienen el mismo rendimiento** "
                "de forma simultánea. Si el valor p es < 0.05, se rechaza la hipótesis nula y "
                "concluimos que al menos un modelo es diferente. En ese caso, el post-hoc de "
                "McNemar con corrección Holm identifica qué pares específicos tienen diferencias.",
                "Cochran's Q test evaluates whether **all models have the same performance** "
                "simultaneously. If the p-value is < 0.05, the null hypothesis is rejected and "
                "we conclude that at least one model is different. In that case, McNemar's post-hoc "
                "with Holm correction identifies which specific pairs differ.",
                "O teste Q de Cochran avalia se **todos os modelos têm o mesmo desempenho** "
                "simultaneamente. Se o valor p for < 0.05, a hipótese nula é rejeitada e "
                "concluímos que pelo menos um modelo é diferente. Nesse caso, o post-hoc de "
                "McNemar com correção de Holm identifica quais pares específicos diferem.",
            ),
            "Bootstrap": _t(
                "Los intervalos de confianza bootstrap al 95% indican el rango donde se encuentra "
                "la **verdadera métrica** con un 95% de confianza. Si los intervalos de dos modelos "
                "no se superponen, es una señal de que sus rendimientos son significativamente "
                "distintos. Intervalos anchos indican mayor incertidumbre en la estimación.",
                "95% bootstrap confidence intervals indicate the range where the **true metric** "
                "lies with 95% confidence. If two models' intervals do not overlap, it suggests "
                "their performances are significantly different. Wide intervals indicate greater "
                "uncertainty in the estimate.",
                "Os intervalos de confiança bootstrap de 95% indicam a faixa onde a **verdadeira métrica** "
                "se encontra com 95% de confiança. Se os intervalos de dois modelos não se sobrepõem, "
                "é um sinal de que seus desempenhos são significativamente diferentes. Intervalos "
                "largos indicam maior incerteza na estimativa.",
            ),
            "Tamaño del Efecto": _t(
                "El tamaño del efecto mide la **magnitud de las diferencias** entre modelos, "
                "independientemente del tamaño de la muestra. Valores grandes indican que la "
                "diferencia entre modelos no solo es estadísticamente significativa, sino también "
                "prácticamente relevante.",
                "Effect size measures the **magnitude of differences** between models, "
                "regardless of sample size. Large values indicate that the difference between "
                "models is not only statistically significant but also practically relevant.",
                "O tamanho do efeito mede a **magnitude das diferenças** entre modelos, "
                "independentemente do tamanho da amostra. Valores grandes indicam que a diferença "
                "entre modelos não é apenas estatisticamente significativa, mas também "
                "praticamente relevante.",
            ),
        }
        for tab, (name, df, desc) in zip(tabs, tests):
            with tab:
                st.markdown(f"*{desc}*")
                st.dataframe(df, use_container_width=True, hide_index=True)
                interprete = interpretaciones.get(name)
                if interprete:
                    st.info(interprete, icon="💡")
    else:
        empty_state("📈", _t("Reportes no encontrados", "Reports not found", "Relatórios não encontrados"),
                     _t("No hay archivos CSV en reports/estadistica/.", "No CSV files in reports/estadistica/.", "Nenhum arquivo CSV em reports/estadistica/."))
