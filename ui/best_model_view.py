"""Best model view — details, artifacts, and status."""

import json
import streamlit as st
from pathlib import Path
from datetime import datetime
from ui.components import section_header, empty_state, info_box, run_script_button, reload_ranking_callback


def _t(es: str, en: str, pt: str) -> str:
    lang = st.session_state.get("language", "es")
    return {"es": es, "en": en, "pt": pt}.get(lang, es)


def _fmt_metric(val) -> str:
    if val is None or val == "":
        return "N/A"
    try:
        v = float(val)
        return f"{v * 100:.2f}%" if v <= 1 else f"{v:.4f}"
    except (TypeError, ValueError):
        return str(val)


def _get_mtime(path: Path) -> str:
    try:
        ts = path.stat().st_mtime
        return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")
    except (OSError, ValueError):
        return "—"


def _check_artifact(path_str: str) -> dict:
    p = Path(path_str)
    exists = p.exists()
    return {
        "path": path_str,
        "exists": exists,
        "size": f"{p.stat().st_size / 1024:.1f} KB" if exists else "—",
        "mtime": _get_mtime(p) if exists else "—",
    }


def render():
    lang = st.session_state.get("language", "es")
    section_header(
        _t("Mejor Modelo", "Best Model", "Melhor Modelo"),
        _t("Modelo seleccionado como óptimo para diagnóstico", "Model selected as optimal for diagnosis", "Modelo selecionado como ótimo para diagnóstico"),
        "⭐",
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
        reload_callback=reload_ranking_callback,
    )

    best_name = st.session_state.get("best_model_name", "") or ""
    ranking = st.session_state.get("ranking_data", []) or []

    # Extraer nombre corto del modelo desde el texto de justificación
    _short_name = ""
    if best_name and best_name.startswith("Mejor modelo seleccionado:"):
        _short_name = best_name.split("Mejor modelo seleccionado:")[1].split("\n")[0].strip()
    elif best_name and "\n" not in best_name:
        _short_name = best_name

    model_final_json = Path("models/modelo_final/modelo_final.json")
    if not model_final_json.exists():
        model_final_json = Path("reports/modelos/modelo_final.json")
    mejor_modelo_txt = Path("reports/modelos/mejor_modelo.txt")

    modelo_info = {}

    if model_final_json.exists():
        try:
            with open(model_final_json, encoding="utf-8") as f:
                modelo_info = json.load(f)
        except Exception:
            pass

    if not modelo_info:
        modelo_info = {
            "name": _short_name or best_name,
            "accuracy": None,
            "f1_macro": None,
            "mcc": None,
            "artifacts": [],
            "selection_criteria": _t("No disponible", "Not available", "Indisponível"),
        }
        match_name = _short_name or best_name
        for r in ranking:
            if match_name and (r.get("modelo", "") in match_name):
                modelo_info["accuracy"] = r.get("accuracy")
                modelo_info["f1_macro"] = r.get("f1_macro") or r.get("f1_score")
                modelo_info["mcc"] = r.get("mcc")
                break

    if modelo_info.get("name") or modelo_info.get("key"):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(_t("Modelo", "Model", "Modelo"),
                      modelo_info.get("name") or modelo_info.get("key", "N/A"))
        with col2:
            st.metric(_t("Tipo", "Type", "Tipo"),
                      modelo_info.get("type", modelo_info.get("tipo", "—")))
        with col3:
            st.metric(_t("Accuracy", "Accuracy", "Acurácia"),
                      _fmt_metric(modelo_info.get("accuracy")))

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("F1-macro", _fmt_metric(modelo_info.get("f1_macro")))
        with col2:
            st.metric("MCC", _fmt_metric(modelo_info.get("mcc")))
        with col3:
            criteria = modelo_info.get("selection_criteria", modelo_info.get("criterio", "—"))
            st.metric(_t("Criterio", "Criteria", "Critério"),
                      criteria if isinstance(criteria, str) and len(criteria) < 30 else _t("MCC + F1 + Acc", "MCC + F1 + Acc", "MCC + F1 + Acc"))

        st.markdown("---")

        artifacts = modelo_info.get("artifacts", [])
        if artifacts:
            st.markdown(f"### {_t('Artefactos del modelo', 'Model artifacts', 'Artefatos do modelo')}")
            for art in artifacts:
                info = _check_artifact(art)
                icon = "✅" if info["exists"] else "❌"
                st.markdown(
                    f"{icon} `{info['path']}`  \n"
                    f"  {_t('Tamaño', 'Size', 'Tamanho')}: {info['size']}  |  "
                    f"{_t('Modificación', 'Modified', 'Modificação')}: {info['mtime']}"
                )
        else:
            modelo_final_dir = Path("reports/modelos/modelo_final")
            if modelo_final_dir.exists():
                st.markdown(f"### {_t('Artefactos del modelo', 'Model artifacts', 'Artefatos do modelo')}")
                for f in sorted(modelo_final_dir.iterdir()):
                    if f.is_file():
                        info = _check_artifact(str(f))
                        icon = "✅" if info["exists"] else "❌"
                        st.markdown(
                            f"{icon} `{f.name}`  —  {info['size']}  —  {info['mtime']}"
                        )

        if mejor_modelo_txt.exists():
            with open(mejor_modelo_txt, encoding="utf-8") as f:
                content = f.read().strip()
            if content and content != best_name:
                st.info(f"📄 {_t('Archivo de selección', 'Selection file', 'Arquivo de seleção')}: {content}")

    elif best_name:
        st.info(f"**{_t('Mejor modelo', 'Best model', 'Melhor modelo')}:** {best_name}")
    else:
        empty_state("⭐", _t("No hay modelo seleccionado", "No model selected", "Nenhum modelo selecionado"),
                     _t("Ejecuta src/seleccion_mejor_modelo.py para seleccionar el mejor modelo.", "Run src/seleccion_mejor_modelo.py to select the best model.", "Execute src/seleccion_mejor_modelo.py para selecionar o melhor modelo."))
