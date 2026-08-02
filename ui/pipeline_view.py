"""Pipeline summary view — detailed stage status with scripts and outputs."""

import streamlit as st
from pathlib import Path
from datetime import datetime
from ui.components import empty_state


PIPELINE_STAGES = [
    {
        "id": "dataset",
        "label_es": "Preparación del dataset",
        "label_en": "Dataset preparation",
        "label_pt": "Preparação do dataset",
        "script": "src/prepare_dataset.py",
        "outputs": ["dataset/train/", "dataset/test/"],
        "check": lambda: Path("dataset/train").exists() and Path("dataset/test").exists(),
    },
    {
        "id": "eda",
        "label_es": "EDA — Análisis exploratorio",
        "label_en": "EDA — Exploratory analysis",
        "label_pt": "EDA — Análise exploratória",
        "script": "src/eda_validacion_datos.py",
        "outputs": ["reports/eda/"],
        "check": lambda: Path("reports/eda/resumen_dataset.csv").exists(),
    },
    {
        "id": "preprocessing",
        "label_es": "Preprocesamiento y aumento",
        "label_en": "Preprocessing & augmentation",
        "label_pt": "Pré-processamento e aumento",
        "script": "src/preprocesamiento_aumento.py",
        "outputs": ["reports/preprocessing/"],
        "check": lambda: Path("reports/preprocessing/ejemplos_aumento_datos.png").exists(),
    },
    {
        "id": "training_m1",
        "label_es": "M1 — SVM",
        "label_en": "M1 — SVM",
        "label_pt": "M1 — SVM",
        "script": "src/train_m1_svm.py",
        "outputs": ["models/svm_model.pkl", "reports/modelos/m1_svm/"],
        "check": lambda: Path("models/svm_model.pkl").exists(),
    },
    {
        "id": "training_m2",
        "label_es": "M2 — Random Forest",
        "label_en": "M2 — Random Forest",
        "label_pt": "M2 — Random Forest",
        "script": "src/train_m2_random_forest.py",
        "outputs": ["models/random_forest_model.pkl", "reports/modelos/m2_random_forest/"],
        "check": lambda: Path("models/random_forest_model.pkl").exists(),
    },
    {
        "id": "training_m3",
        "label_es": "M3 — KNN",
        "label_en": "M3 — KNN",
        "label_pt": "M3 — KNN",
        "script": "src/train_m3_knn.py",
        "outputs": ["models/knn_model.pkl", "reports/modelos/m3_knn/"],
        "check": lambda: Path("models/knn_model.pkl").exists(),
    },
    {
        "id": "training_h1",
        "label_es": "H1 — CNN + SVM",
        "label_en": "H1 — CNN + SVM",
        "label_pt": "H1 — CNN + SVM",
        "script": "src/train_h1_cnn_svm.py",
        "outputs": ["models/cnn_feature_extractor.h5", "models/cnn_svm_model.pkl", "reports/modelos/h1_cnn_svm/"],
        "check": lambda: Path("models/cnn_feature_extractor.h5").exists(),
    },
    {
        "id": "training_h2",
        "label_es": "H2 — MobileNetV2 + RF",
        "label_en": "H2 — MobileNetV2 + RF",
        "label_pt": "H2 — MobileNetV2 + RF",
        "script": "src/train_h2_transfer_random_forest.py",
        "outputs": ["models/transfer_feature_extractor.h5", "models/transfer_random_forest_model.pkl", "reports/modelos/h2_transfer_rf/"],
        "check": lambda: Path("models/transfer_feature_extractor.h5").exists(),
    },
    {
        "id": "crossval",
        "label_es": "Validación cruzada",
        "label_en": "Cross-validation",
        "label_pt": "Validação cruzada",
        "script": "src/cross_validation_modelos.py",
        "outputs": ["reports/modelos/cross_validation/"],
        "check": lambda: Path("reports/modelos/cross_validation/cross_validation_resultados.csv").exists(),
    },
    {
        "id": "hyperparams",
        "label_es": "Optimización de hiperparámetros",
        "label_en": "Hyperparameter optimization",
        "label_pt": "Otimização de hiperparâmetros",
        "script": "src/optimizacion_hiperparametros.py",
        "outputs": ["reports/modelos/tuning/"],
        "check": lambda: Path("reports/modelos/tuning/").exists() and any(Path("reports/modelos/tuning/").iterdir()),
    },
    {
        "id": "stats",
        "label_es": "Pruebas estadísticas",
        "label_en": "Statistical tests",
        "label_pt": "Testes estatísticos",
        "script": "src/validacion_estadistica_modelos.py",
        "outputs": ["reports/estadistica/"],
        "check": lambda: Path("reports/estadistica/tamano_efecto.csv").exists(),
    },
    {
        "id": "comparison",
        "label_es": "Evaluación comparativa",
        "label_en": "Comparative evaluation",
        "label_pt": "Avaliação comparativa",
        "script": "src/evaluacion_comparativa.py",
        "outputs": ["reports/modelos/comparativos/"],
        "check": lambda: Path("reports/modelos/ranking_modelos.csv").exists(),
    },
    {
        "id": "best_model",
        "label_es": "Selección del mejor modelo",
        "label_en": "Best model selection",
        "label_pt": "Seleção do melhor modelo",
        "script": "src/seleccion_mejor_modelo.py",
        "outputs": ["reports/modelos/mejor_modelo.txt", "reports/modelos/ranking_modelos.csv"],
        "check": lambda: Path("reports/modelos/mejor_modelo.txt").exists(),
    },
]


def _t(es: str, en: str, pt: str) -> str:
    lang = st.session_state.get("language", "es")
    return {"es": es, "en": en, "pt": pt}.get(lang, es)


def _get_mtime(path: Path) -> str:
    try:
        ts = path.stat().st_mtime
        return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")
    except (OSError, ValueError):
        return "—"


def _get_outputs_mtime(outputs: list) -> str:
    """Retorna la última modificación entre todas las salidas de la etapa."""
    timestamps = []
    for out in outputs:
        p = Path(out)
        if not p.exists():
            continue
        if p.is_dir():
            for f in p.rglob("*"):
                if f.is_file():
                    try:
                        timestamps.append(f.stat().st_mtime)
                    except OSError:
                        pass
        else:
            try:
                timestamps.append(p.stat().st_mtime)
            except OSError:
                pass
    if not timestamps:
        return "—"
    return datetime.fromtimestamp(max(timestamps)).strftime("%Y-%m-%d %H:%M")


def _render_stage_card(stage: dict, completed: bool):
    label = stage.get(f"label_{st.session_state.get('language', 'es')}", stage["label_es"])
    icon = "✅" if completed else "⬜"
    status_text = _t("Completado", "Completed", "Concluído") if completed else _t("Pendiente", "Pending", "Pendente")
    status_color = "var(--green-primary)" if completed else "var(--text-muted)"

    with st.expander(f"{icon} {label}", expanded=False):
        st.markdown(f"**{_t('Script', 'Script', 'Script')}:** `{stage['script']}")
        st.markdown(f"**{_t('Última modificación', 'Last modified', 'Última modificação')}:** {_get_outputs_mtime(stage['outputs'])}")

        st.markdown(f"**{_t('Salidas generadas', 'Generated outputs', 'Saídas geradas')}:**")
        for out in stage["outputs"]:
            out_path = Path(out)
            exists = out_path.exists()
            icon_o = "✅" if exists else "⬜"
            st.markdown(f"  {icon_o} `{out}`")

        st.markdown(
            f"**{_t('Estado', 'Status', 'Status')}:** "
            f"<span style='color:{status_color};font-weight:600;'>{status_text}</span>",
            unsafe_allow_html=True,
        )


def render():
    any_running = any(
        v for k, v in st.session_state.items()
        if k.startswith("_running_") and v
    )

    if st.button(
        _t("🔄 Actualizar estado", "🔄 Refresh status", "🔄 Atualizar status"),
        key="refresh_pipeline",
        disabled=any_running,
    ):
        st.rerun()

    total = len(PIPELINE_STAGES)
    completed = sum(1 for s in PIPELINE_STAGES if s["check"]())
    pct = int(completed / total * 100) if total > 0 else 0

    st.progress(pct / 100, text=f"{completed}/{total} {_t('etapas completadas', 'stages completed', 'etapas concluídas')}")

    st.markdown("---")

    for stage in PIPELINE_STAGES:
        done = stage["check"]()
        _render_stage_card(stage, done)
