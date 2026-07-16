"""Pipeline status view showing experiment stages."""

import streamlit as st
import pandas as pd
from pathlib import Path
from ui.components import section_header, stepper, status_badge, empty_state


def render():
    lang = st.session_state.get("language", "es")
    section_header(
        "Estado del Pipeline",
        "Progreso del flujo de experimentación",
        "🔧",
    )

    statuses = check_pipeline_status()

    steps = [
        {
            "label": "Preparación del dataset",
            "key": "dataset",
            "files": [Path("dataset/train"), Path("dataset/test")],
        },
        {
            "label": "EDA - Análisis exploratorio",
            "key": "eda",
            "files": [Path("reports/eda/resumen_dataset.csv"), Path("reports/eda/distribucion_clases.png")],
        },
        {
            "label": "Preprocesamiento y aumento",
            "key": "preprocessing",
            "files": [Path("reports/preprocessing/ejemplos_aumento_datos.png")],
        },
        {
            "label": "Entrenamiento de modelos",
            "key": "training",
            "files": [Path("reports/modelos/m1_svm/resultados_m1_svm.csv")],
        },
        {
            "label": "Validación cruzada (5-folds)",
            "key": "crossval",
            "files": [Path("reports/modelos/cross_validation/cross_validation_resultados.csv")],
        },
        {
            "label": "Optimización de hiperparámetros",
            "key": "hyperparam",
            "files": [Path("reports/modelos/tuning/mejores_hiperparametros.csv")],
        },
        {
            "label": "Validación estadística",
            "key": "statistical",
            "files": [Path("reports/estadistica/mcnemar_resultados.csv")],
        },
        {
            "label": "Selección del mejor modelo",
            "key": "model_selection",
            "files": [Path("reports/modelos/ranking_modelos.csv")],
        },
        {
            "label": "Despliegue",
            "key": "deploy",
            "files": [Path("app.py")],
        },
    ]

    all_done = True
    for i, step in enumerate(steps):
        done = all(f.exists() for f in step["files"])
        if not done:
            all_done = False
        status_key = "completed" if done else ("running" if i > 0 and all(
            all(f.exists() for f in steps[j]["files"]) for j in range(i)
        ) else "pending")
        step["status"] = status_key
        step["detail"] = "Completado" if done else "Pendiente"

    stepper(steps)

    st.markdown("### Resumen del Pipeline")
    if statuses:
        cols = st.columns(3)
        status_labels = {
            "completed": ("✅ Completado", "var(--green-primary)"),
            "running": ("🔄 En progreso", "var(--blue)"),
            "pending": ("⬜ Pendiente", "var(--text-muted)"),
            "error": ("❌ Error", "var(--red)"),
        }
        for i, (key, st_info) in enumerate(statuses.items()):
            done = st_info.get("done", False)
            label = st_info.get("label", key)
            icon = "✅" if done else "⬜"
            with cols[i % 3]:
                st.markdown(f"{icon} **{label}**")
    else:
        empty_state("🔧", "Pipeline no disponible", "No se encontraron reportes de pipeline.")


def check_pipeline_status():
    checks = {
        "eda": {
            "label_es": "EDA - Análisis exploratorio",
            "label_en": "EDA - Exploratory analysis",
            "label_pt": "EDA - Análise exploratória",
            "files": [Path("reports/eda/resumen_dataset.csv"), Path("reports/eda/distribucion_clases.png")],
        },
        "preprocessing": {
            "label_es": "Preprocesamiento y aumento",
            "label_en": "Preprocessing & augmentation",
            "label_pt": "Pré-processamento e aumento",
            "files": [Path("reports/preprocessing/ejemplos_aumento_datos.png")],
        },
        "crossval": {
            "label_es": "Validación cruzada (5-folds)",
            "label_en": "Cross-validation (5-fold)",
            "label_pt": "Validação cruzada (5-fold)",
            "files": [Path("reports/modelos/cross_validation/cross_validation_resultados.csv")],
        },
        "hyperparam": {
            "label_es": "Optimización de hiperparámetros",
            "label_en": "Hyperparameter optimization",
            "label_pt": "Otimização de hiperparâmetros",
            "files": [Path("reports/modelos/tuning/mejores_hiperparametros.csv")],
        },
        "statistical": {
            "label_es": "Validación estadística",
            "label_en": "Statistical validation",
            "label_pt": "Validação estatística",
            "files": [Path("reports/estadistica/mcnemar_resultados.csv")],
        },
        "model_selection": {
            "label_es": "Selección del mejor modelo",
            "label_en": "Best model selection",
            "label_pt": "Seleção do melhor modelo",
            "files": [Path("reports/modelos/ranking_modelos.csv")],
        },
    }
    lang = st.session_state.get("language", "es")
    results = {}
    for key, check in checks.items():
        done = all(f.exists() for f in check["files"])
        label = check.get(f"label_{lang}", check["label_es"])
        results[key] = {"done": done, "label": label}
    return results
