"""Statistical tests view — Cochran Q, McNemar+Holm, Bootstrap, Effect Size."""

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


def _fmt_p(val: float) -> str:
    if pd.isna(val):
        return "—"
    if val < 0.0001:
        return "< 0.0001"
    return f"{val:.6f}"


def _fmt_p4(val: float) -> str:
    if pd.isna(val):
        return "—"
    if val < 0.0001:
        return "< 0.0001"
    return f"{val:.4f}"


def _render_cochran():
    df = _read_csv("cochran_q_resultado.csv")
    if df is None or df.empty:
        empty_state(
            "📊",
            _t("Cochran Q no disponible", "Cochran Q not available", "Cochran Q indisponível"),
            _t("Ejecuta las pruebas estadísticas para generar este reporte.",
               "Run the statistical tests to generate this report.",
               "Execute os testes estatísticos para gerar este relatório."),
        )
        return

    cols = {"estadistico_Q": "Estadístico Q", "p_value": "Valor p",
            "interpretacion": "Interpretación", "k": "Modelos comparados",
            "n": "Imágenes evaluadas"}
    mostrar = df[list(cols.keys())].copy()
    mostrar.columns = list(cols.values())
    if "Valor p" in mostrar.columns:
        mostrar["Valor p"] = mostrar["Valor p"].apply(_fmt_p)

    st.markdown("**Prueba de Cochran Q — Comparación global simultánea**")
    st.dataframe(mostrar, use_container_width=True, hide_index=True)

    p_val = df["p_value"].iloc[0] if "p_value" in df.columns else 1.0
    info_box(
        _t(
            "Cochran Q determina si existe una diferencia global entre los modelos evaluados "
            "sobre las mismas imágenes de prueba.",
            "Cochran Q determines whether there is a global difference among the models evaluated "
            "on the same test images.",
            "O Q de Cochran determina se existe uma diferença global entre os modelos avaliados "
            "nas mesmas imagens de teste.",
        ),
        type_="info",
    )
    if p_val < 0.05:
        info_box(
            _t(
                "Cochran Q es significativo (p < 0.05). Corresponde revisar el post-hoc "
                "McNemar + Holm en la siguiente pestaña.",
                "Cochran Q is significant (p < 0.05). Check the McNemar + Holm post-hoc "
                "in the next tab.",
                "Cochran Q é significativo (p < 0.05). Confira o post-hoc McNemar + Holm "
                "na próxima aba.",
            ),
            type_="success",
        )


def _render_holm():
    df = _read_csv("mcnemar_holm_posthoc.csv")
    if df is None or df.empty:
        empty_state(
            "📊",
            _t("McNemar + Holm no disponible", "McNemar + Holm not available", "McNemar + Holm indisponível"),
            _t("Cochran Q debe ser significativo para generar este reporte. "
               "Ejecuta las pruebas estadísticas primero.",
               "Cochran Q must be significant to generate this report. "
               "Run the statistical tests first.",
               "Cochran Q deve ser significativo para gerar este relatório. "
               "Execute os testes estatísticos primeiro."),
        )
        return

    cols = {"n1": "Modelo 1", "n2": "Modelo 2", "b": "Acierta M1 / falla M2",
            "c": "Falla M1 / acierta M2", "statistic": "Estadístico",
            "p_raw": "Valor p original", "p_holm": "Valor p ajustado",
            "metodo": "Método", "significativo": "¿Diferencia significativa?"}
    mostrar = df[list(cols.keys())].copy()
    mostrar.columns = list(cols.values())
    mostrar["Valor p original"] = mostrar["Valor p original"].apply(_fmt_p)
    mostrar["Valor p ajustado"] = mostrar["Valor p ajustado"].apply(_fmt_p4)

    favorecido = []
    for _, row in df.iterrows():
        if row["b"] > row["c"]:
            favorecido.append(row["n1"])
        elif row["c"] > row["b"]:
            favorecido.append(row["n2"])
        else:
            favorecido.append("Empate")
    mostrar["Modelo favorecido"] = favorecido

    st.markdown("**McNemar post-hoc con corrección Holm — Comparaciones por pares**")
    st.dataframe(mostrar, use_container_width=True, hide_index=True)

    info_box(
        _t(
            "La corrección Holm controla el error producido por realizar múltiples "
            "comparaciones. Las conclusiones deben basarse en el valor p ajustado.",
            "Holm correction controls the error from performing multiple comparisons. "
            "Conclusions should be based on the adjusted p-value.",
            "A correção de Holm controla o erro produzido ao realizar múltiplas "
            "comparações. As conclusões devem basear-se no valor p ajustado.",
        ),
        type_="info",
    )


def _render_bootstrap():
    df = _read_csv("intervalos_confianza_bootstrap.csv")
    if df is None or df.empty:
        empty_state(
            "📊",
            _t("Bootstrap no disponible", "Bootstrap not available", "Bootstrap indisponível"),
            _t("Ejecuta las pruebas estadísticas para generar este reporte.",
               "Run the statistical tests to generate this report.",
               "Execute os testes estatísticos para gerar este relatório."),
        )
        return

    cols = {"modelo": "Modelo", "acc_media": "Accuracy media",
            "acc_ci_inf": "Accuracy IC inferior", "acc_ci_sup": "Accuracy IC superior",
            "f1_media": "F1-macro medio", "f1_ci_inf": "F1 IC inferior",
            "f1_ci_sup": "F1 IC superior", "mcc_media": "MCC medio",
            "mcc_ci_inf": "MCC IC inferior", "mcc_ci_sup": "MCC IC superior"}
    mostrar = df[list(cols.keys())].copy()
    mostrar.columns = list(cols.values())
    mostrar = mostrar.sort_values("MCC medio", ascending=False).reset_index(drop=True)

    for c in mostrar.columns:
        if c != "Modelo":
            mostrar[c] = mostrar[c].apply(lambda x: round(x, 4) if pd.notna(x) else x)

    st.markdown("**Intervalos de confianza Bootstrap estratificado (95%)**")
    st.dataframe(mostrar, use_container_width=True, hide_index=True)

    if not mostrar.empty:
        best_model = mostrar.iloc[0]["Modelo"]
        best_mcc = mostrar.iloc[0]["MCC medio"]
        info_box(
            _t(
                f"Modelo con mayor MCC: **{best_model}** ({best_mcc:.4f}). "
                "Intervalos más altos y estrechos indican mejor rendimiento y mayor estabilidad.",
                f"Model with highest MCC: **{best_model}** ({best_mcc:.4f}). "
                "Higher and narrower intervals indicate better performance and greater stability.",
                f"Modelo com maior MCC: **{best_model}** ({best_mcc:.4f}). "
                "Intervalos mais altos e estreitos indicam melhor desempenho e maior estabilidade.",
            ),
            type_="success",
        )

    info_box(
        _t(
            "El bootstrap estima la estabilidad de Accuracy, F1-macro y MCC mediante 1000 "
            "remuestreos estratificados. Intervalos más altos y estrechos indican mejor "
            "rendimiento y mayor estabilidad.",
            "Bootstrap estimates the stability of Accuracy, F1-macro and MCC using 1000 "
            "stratified resamples. Higher and narrower intervals indicate better performance "
            "and greater stability.",
            "O bootstrap estima a estabilidade de Accuracy, F1-macro e MCC usando 1000 "
            "reamostragens estratificadas. Intervalos mais altos e estreitos indicam melhor "
            "desempenho e maior estabilidade.",
        ),
        type_="info",
    )


def _render_effect_size():
    df = _read_csv("tamano_efecto.csv")
    if df is None or df.empty:
        empty_state(
            "📊",
            _t("Tamaño del efecto no disponible", "Effect size not available", "Tamanho do efeito indisponível"),
            _t("Ejecuta las pruebas estadísticas para generar este reporte.",
               "Run the statistical tests to generate this report.",
               "Execute os testes estatísticos para gerar este relatório."),
        )
        return

    cols = {"modelo_1": "Modelo 1", "modelo_2": "Modelo 2",
            "diff_accuracy_modelo1_menos_modelo2": "Diferencia Accuracy",
            "abs_diff_accuracy": "Diferencia absoluta Accuracy",
            "diff_f1_macro_modelo1_menos_modelo2": "Diferencia F1-macro",
            "diff_mcc_modelo1_menos_modelo2": "Diferencia MCC",
            "odds_ratio_mcnemar_cc": "Odds ratio"}
    mostrar = df[list(cols.keys())].copy()
    mostrar.columns = list(cols.values())

    favorecido = []
    for _, row in df.iterrows():
        diff_mcc = row.get("diff_mcc_modelo1_menos_modelo2", 0)
        if diff_mcc > 0:
            favorecido.append(row["modelo_1"])
        elif diff_mcc < 0:
            favorecido.append(row["modelo_2"])
        else:
            favorecido.append("Empate")
    mostrar["Modelo favorecido"] = favorecido

    mostrar = mostrar.sort_values("Diferencia absoluta Accuracy", ascending=False).reset_index(drop=True)

    for c in mostrar.columns:
        if c not in ("Modelo 1", "Modelo 2", "Modelo favorecido"):
            mostrar[c] = mostrar[c].apply(lambda x: round(x, 4) if pd.notna(x) else x)

    st.markdown("**Tamaño del efecto — Magnitud de las diferencias entre modelos**")
    st.dataframe(mostrar, use_container_width=True, hide_index=True)

    info_box(
        _t(
            "El tamaño del efecto indica cuánto difieren los modelos en la práctica. "
            "Un resultado estadísticamente significativo puede tener una diferencia "
            "pequeña, por eso debe revisarse junto con esta tabla.",
            "Effect size indicates how much models differ in practice. "
            "A statistically significant result may have a small difference, "
            "so it should be reviewed together with this table.",
            "O tamanho do efeito indica quanto os modelos diferem na prática. "
            "Um resultado estatisticamente significativo pode ter uma diferença "
            "pequena, por isso deve ser revisado junto com esta tabela.",
        ),
        type_="info",
    )


def render():
    lang = st.session_state.get("language", "es")
    section_header(
        _t("Validación Estadística", "Statistical Validation", "Validação Estatística"),
        _t("Pruebas estadísticas del rendimiento de los modelos",
          "Statistical tests of model performance",
          "Testes estatísticos do desempenho dos modelos"),
        "📈",
    )

    run_script_button(
        "src/validacion_estadistica_modelos.py",
        _t("📈 Ejecutar pruebas estadísticas", "📈 Run statistical tests", "📈 Executar testes estatísticos"),
        key="run_stats",
        confirm_message=_t(
            "¿Ejecutar todas las pruebas estadísticas (Cochran Q, McNemar+Holm, Bootstrap, etc.)?",
            "Run all statistical tests (Cochran Q, McNemar+Holm, Bootstrap, etc.)?",
            "Executar todos os testes estatísticos (Cochran Q, McNemar+Holm, Bootstrap, etc.)?",
        ),
    )

    if not STAT_DIR.exists():
        empty_state(
            "📈",
            _t("Pruebas estadísticas no disponibles",
               "Statistical tests not available",
               "Testes estatísticos indisponíveis"),
            _t("Ejecuta src/validacion_estadistica_modelos.py para generar los reportes.",
               "Run src/validacion_estadistica_modelos.py to generate reports.",
               "Execute src/validacion_estadistica_modelos.py para gerar relatórios."),
        )
        return

    tab_cochran, tab_holm, tab_bootstrap, tab_effect = st.tabs([
        "1. Cochran Q",
        "2. McNemar + Holm",
        "3. Bootstrap",
        "4. Tamaño del efecto",
    ])

    with tab_cochran:
        _render_cochran()

    with tab_holm:
        _render_holm()

    with tab_bootstrap:
        _render_bootstrap()

    with tab_effect:
        _render_effect_size()
