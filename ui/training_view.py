"""Training view — model cards with metrics, artifacts, and status."""

import streamlit as st
import pandas as pd
from pathlib import Path
from ui.components import empty_state, info_box, run_script_button, reload_ranking_callback


MODELS = [
    {
        "key": "M1",
        "name": "M1 — SVM",
        "type_es": "Clásico",
        "type_en": "Classic",
        "type_pt": "Clássico",
        "script": "src/train_m1_svm.py",
        "artifacts": ["models/svm_model.pkl", "models/svm_scaler.pkl"],
        "reports_dir": Path("reports/modelos/m1_svm"),
        "check": lambda: Path("models/svm_model.pkl").exists(),
    },
    {
        "key": "M2",
        "name": "M2 — Random Forest",
        "type_es": "Clásico",
        "type_en": "Classic",
        "type_pt": "Clássico",
        "script": "src/train_m2_random_forest.py",
        "artifacts": ["models/random_forest_model.pkl"],
        "reports_dir": Path("reports/modelos/m2_random_forest"),
        "check": lambda: Path("models/random_forest_model.pkl").exists(),
    },
    {
        "key": "M3",
        "name": "M3 — KNN",
        "type_es": "Clásico",
        "type_en": "Classic",
        "type_pt": "Clássico",
        "script": "src/train_m3_knn.py",
        "artifacts": ["models/knn_model.pkl", "models/knn_scaler.pkl"],
        "reports_dir": Path("reports/modelos/m3_knn"),
        "check": lambda: Path("models/knn_model.pkl").exists(),
    },
    {
        "key": "H1",
        "name": "H1 — CNN + SVM",
        "type_es": "Híbrido",
        "type_en": "Hybrid",
        "type_pt": "Híbrido",
        "script": "src/train_h1_cnn_svm.py",
        "artifacts": ["models/cnn_feature_extractor.h5", "models/cnn_svm_model.pkl"],
        "reports_dir": Path("reports/modelos/h1_cnn_svm"),
        "check": lambda: Path("models/cnn_feature_extractor.h5").exists(),
    },
    {
        "key": "H2",
        "name": "H2 — MobileNetV2 + RF",
        "type_es": "Híbrido",
        "type_en": "Hybrid",
        "type_pt": "Híbrido",
        "script": "src/train_h2_transfer_random_forest.py",
        "artifacts": ["models/transfer_feature_extractor.h5", "models/transfer_random_forest_model.pkl"],
        "reports_dir": Path("reports/modelos/h2_transfer_rf"),
        "check": lambda: Path("models/transfer_feature_extractor.h5").exists(),
    },
]


def _t(es: str, en: str, pt: str) -> str:
    lang = st.session_state.get("language", "es")
    return {"es": es, "en": en, "pt": pt}.get(lang, es)


def _get_metrics(model_key: str) -> dict:
    ranking = st.session_state.get("ranking_data", []) or []
    for r in ranking:
        if r.get("modelo") and model_key in r.get("modelo", ""):
            return {
                "accuracy": r.get("accuracy"),
                "precision": r.get("precision"),
                "recall": r.get("recall"),
                "f1_score": r.get("f1_score"),
                "mcc": r.get("mcc"),
            }
    return {}


def _fmt_metric(val) -> str:
    if val is None or val == "":
        return "N/A"
    try:
        return f"{float(val):.4f}"
    except (TypeError, ValueError):
        return str(val)


def mantener_modelo_abierto(model_key: str):
    st.session_state[f"model_expanded_{model_key}"] = True


def _render_model_card(model: dict):
    trained = model["check"]()
    icon = "✅" if trained else "⬜"
    type_key = f"type_{st.session_state.get('language', 'es')}"
    model_type = model.get(type_key, model["type_es"])
    state_key = f"model_expanded_{model['key']}"
    button_key = f"toggle_model_{model['key']}"
    if state_key not in st.session_state:
        st.session_state[state_key] = False
    expanded = st.session_state[state_key]

    col1, col2 = st.columns([0.9, 0.1])
    with col1:
        st.markdown(f"### {icon} {model['name']}  —  _{model_type}_")
    with col2:
        label = "▲" if expanded else "▼"
        if st.button(label, key=button_key, use_container_width=True):
            st.session_state[state_key] = not st.session_state[state_key]
            st.rerun()

    if expanded:
        st.markdown(f"**{_t('Script', 'Script', 'Script')}:** `{model['script']}`")

        run_script_button(
            model["script"],
            _t(f"🚀 Entrenar {model['key']}", f"🚀 Train {model['key']}", f"🚀 Treinar {model['key']}"),
            key=f"train_{model['key']}",
            confirm_message=_t(
                f"¿Ejecutar {model['script']}? Puede tomar varios minutos.",
                f"Run {model['script']}? This may take several minutes.",
                f"Executar {model['script']}? Pode levar vários minutos.",
            ),
            heavy=(model["key"] in ("H1", "H2")),
            reload_callback=reload_ranking_callback,
            on_start=lambda: mantener_modelo_abierto(model["key"]),
        )

        st.markdown(f"**{_t('Artefactos', 'Artifacts', 'Artefatos')}:**")
        for art in model["artifacts"]:
            art_path = Path(art)
            exists = art_path.exists()
            icon_a = "✅" if exists else "⬜"
            size = f"{art_path.stat().st_size / 1024:.1f} KB" if exists else ""
            st.markdown(f"  {icon_a} `{art}`  {size}")

        if trained:
            metrics = _get_metrics(model["key"])
            if metrics and any(v is not None for v in metrics.values()):
                st.markdown(f"**{_t('Métricas', 'Metrics', 'Métricas')}**")
                cols = st.columns(5)
                metric_names = {
                    "accuracy": _t("Accuracy", "Accuracy", "Acurácia"),
                    "precision": _t("Precision", "Precision", "Precisão"),
                    "recall": _t("Recall", "Recall", "Recall"),
                    "f1_score": _t("F1-macro", "F1-macro", "F1-macro"),
                    "mcc": _t("MCC", "MCC", "MCC"),
                }
                for i, (k, label) in enumerate(metric_names.items()):
                    with cols[i]:
                        st.metric(label, _fmt_metric(metrics.get(k)))

            reports_dir = model["reports_dir"]
            if reports_dir.exists():
                cm_files = sorted(reports_dir.glob("confusion_*.png"))
                roc_files = sorted(reports_dir.glob("roc_*.png"))
                pr_files = sorted(reports_dir.glob("precision_recall_*.png"))

                if cm_files:
                    st.markdown(f"**{_t('Matriz de confusión', 'Confusion matrix', 'Matriz de confusão')}**")
                    for f in cm_files:
                        st.image(str(f), use_column_width=True, caption=f.stem)

                if roc_files:
                    st.markdown(f"**{_t('Curva ROC', 'ROC curve', 'Curva ROC')}**")
                    for f in roc_files:
                        st.image(str(f), use_column_width=True, caption=f.stem)

                if pr_files:
                    st.markdown(f"**{_t('Curva Precision-Recall', 'Precision-Recall curve', 'Curva Precision-Recall')}**")
                    for f in pr_files:
                        st.image(str(f), use_column_width=True, caption=f.stem)

                csv_results = list(reports_dir.glob("resultados_*.csv")) + list(reports_dir.glob("*resultados*.csv"))
                if csv_results:
                    st.markdown(f"**{_t('Resultados detallados', 'Detailed results', 'Resultados detalhados')}**")
                    for csv_f in csv_results:
                        try:
                            df = pd.read_csv(csv_f)
                            st.dataframe(df, use_container_width=True, hide_index=True)
                        except Exception:
                            pass
        else:
            info_box(_t("Modelo no entrenado. Ejecuta el script correspondiente.", "Model not trained. Run the corresponding script.", "Modelo não treinado. Execute o script correspondente."), "warning")


def render():
    run_script_button(
        "scripts/train_all.py",
        _t("🔥 Entrenar todos los modelos", "🔥 Train all models", "🔥 Treinar todos os modelos"),
        key="train_all",
        confirm_message=_t(
            "¿Ejecutar los 5 entrenamientos en secuencia? Este proceso puede tomar más de 2 horas en CPU.",
            "Run all 5 training scripts sequentially? This may take over 2 hours on CPU.",
            "Executar os 5 treinamentos em sequência? Este processo pode levar mais de 2 horas em CPU.",
        ),
        heavy=True,
        reload_callback=reload_ranking_callback,
    )

    st.info(_t("Los modelos no se entrenan automáticamente al abrir esta vista. Usa los botones para iniciar cada entrenamiento.", "Models are not trained automatically when opening this view. Use the buttons to start each training.", "Os modelos não são treinados automaticamente ao abrir esta visualização. Use os botões para iniciar cada treinamento."))

    for model in MODELS:
        _render_model_card(model)
