"""Best model view — structured display from modelo_final.json."""

import json
import streamlit as st
from pathlib import Path
from ui.components import section_header, empty_state, info_box, run_script_button

JSON_PATH = Path("models/modelo_final/modelo_final.json")


def _t(es: str, en: str, pt: str) -> str:
    lang = st.session_state.get("language", "es")
    return {"es": es, "en": en, "pt": pt}.get(lang, es)


def _fmt_metric(val) -> str:
    if val is None:
        return "N/A"
    try:
        return f"{float(val):.4f}"
    except (TypeError, ValueError):
        return str(val)


def render():
    lang = st.session_state.get("language", "es")
    section_header(
        _t("⭐ Mejor Modelo", "⭐ Best Model", "⭐ Melhor Modelo"),
        _t("Modelo seleccionado como óptimo para diagnóstico",
          "Model selected as optimal for diagnosis",
          "Modelo selecionado como ótimo para diagnóstico"),
    )

    run_script_button(
        "src/seleccion_mejor_modelo.py",
        _t("⭐ Seleccionar mejor modelo", "⭐ Select best model", "⭐ Selecionar melhor modelo"),
        key="select_best_model",
        confirm_message=_t(
            "¿Ejecutar selección del mejor modelo? Esto evaluará el ranking y elegirá el óptimo.",
            "Run best model selection? This will evaluate the ranking and choose the optimal one.",
            "Executar seleção do melhor modelo? Isso avaliará o ranking e escolherá o ideal.",
        ),
    )

    if not JSON_PATH.exists():
        empty_state(
            "⭐",
            _t("No hay modelo seleccionado", "No model selected", "Nenhum modelo selecionado"),
            _t("Ejecuta src/seleccion_mejor_modelo.py para seleccionar el mejor modelo.",
              "Run src/seleccion_mejor_modelo.py to select the best model.",
              "Execute src/seleccion_mejor_modelo.py para selecionar o melhor modelo."),
        )
        return

    try:
        with open(JSON_PATH, encoding="utf-8") as f:
            info = json.load(f)
    except Exception:
        empty_state(
            "⚠️",
            _t("Error al leer el manifiesto", "Error reading manifest", "Erro ao ler o manifesto"),
            _t("Reintenta ejecutando src/seleccion_mejor_modelo.py.",
              "Try running src/seleccion_mejor_modelo.py again.",
              "Tente executar src/seleccion_mejor_modelo.py novamente."),
        )
        return

    modelo = info.get("modelo_ganador", "—")
    metricas = info.get("metricas_test", {})
    victorias = info.get("victorias_significativas_holm", 0)
    requiere = info.get("requiere_reentrenamiento", True)
    artefactos = info.get("artefactos", [])

    # ── Nombre del ganador ──────────────────────────────────────────
    st.markdown(f"## 🏆 {modelo}")

    # ── Métricas en columnas ────────────────────────────────────────
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Accuracy", _fmt_metric(metricas.get("accuracy")))
    with col2:
        st.metric("F1-macro", _fmt_metric(metricas.get("f1_macro")))
    with col3:
        st.metric("MCC", _fmt_metric(metricas.get("mcc")))

    st.caption(
        _t(
            "Las métricas mostradas corresponden a las medias estimadas mediante Bootstrap sobre el conjunto TEST.",
            "The metrics shown are bootstrap-estimated means on the TEST set.",
            "As métricas mostradas são médias estimadas por Bootstrap no conjunto TEST.",
        )
    )

    # ── Victorias significativas ────────────────────────────────────
    st.markdown(
        _t(
            f"El modelo obtuvo **{victorias}** victorias significativas frente a los demás "
            f"modelos después de aplicar la corrección Holm.",
            f"The model obtained **{victorias}** significant victories over the other "
            f"models after Holm correction.",
            f"O modelo obteve **{victorias}** vitórias significativas sobre os demais "
            f"modelos após a correção de Holm.",
        )
    )

    # ── Estado de persistencia ──────────────────────────────────────
    if not requiere:
        st.success(
            _t(
                "✅ Modelo persistido y listo para inferencia",
                "✅ Model persisted and ready for inference",
                "✅ Modelo persistido e pronto para inferência",
            )
        )

    # ── Criterio de selección ───────────────────────────────────────
    info_box(
        _t(
            "El ranking prioriza MCC. En caso de empate, utiliza F1-macro y luego Accuracy.",
            "Ranking prioritizes MCC. In case of a tie, it uses F1-macro and then Accuracy.",
            "O ranking prioriza MCC. Em caso de empate, utiliza F1-macro e depois Accuracy.",
        ),
        type_="info",
    )

    # ── Artefactos ──────────────────────────────────────────────────
    if artefactos:
        with st.expander(
            _t("Artefactos del modelo final", "Final model artifacts", "Artefatos do modelo final"),
        ):
            for art in artefactos:
                st.markdown(f"- {art.get('tipo', '—').capitalize()}: `{art.get('nombre_archivo', '—')}`")
