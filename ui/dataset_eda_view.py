"""Dataset & EDA view — shows reports/eda/ content and dataset structure."""

import streamlit as st
import pandas as pd
from pathlib import Path
from ui.components import empty_state, info_box, run_script_button, BASE_DIR


EDA_DIR = Path("reports/eda")


def _t(es: str, en: str, pt: str) -> str:
    lang = st.session_state.get("language", "es")
    return {"es": es, "en": en, "pt": pt}.get(lang, es)


def _read_csv(path: Path) -> pd.DataFrame | None:
    if not path.exists():
        return None
    try:
        return pd.read_csv(path)
    except Exception:
        return None


def _show_dataset_dirs():
    st.markdown("### Directorios del dataset")
    dirs = [
        ("dataset_original/", Path("dataset_original")),
        ("dataset/train/", Path("dataset/train")),
        ("dataset/test/", Path("dataset/test")),
    ]
    cols = st.columns(3)
    for col, (label, path) in zip(cols, dirs):
        with col:
            exists = path.exists()
            icon = "✅" if exists else "⬜"
            st.markdown(f"{icon} **`{label}`**")
            if exists:
                n_dirs = len([p for p in path.iterdir() if p.is_dir()]) if path.is_dir() else 0
                n_files = len(list(path.rglob("*"))) if path.is_dir() else 0
                st.caption(f"{n_dirs} {_t('clases', 'classes', 'classes')} | {n_files} {_t('archivos', 'files', 'arquivos')}")
            else:
                st.caption(_t("No disponible", "Not available", "Indisponível"))


def render():
    col1, col2 = st.columns(2)
    with col1:
        run_script_button(
            "src/prepare_dataset.py",
            _t("📦 Preparar dataset", "📦 Prepare dataset", "📦 Preparar dataset"),
            key="prepare_dataset",
            heavy=False,
            confirm_message=_t("¿Recrear la división train/test desde cero?", "Recreate train/test split from scratch?", "Recriar a divisão treino/teste do zero?"),
        )
    with col2:
        run_script_button(
            "src/eda_validacion_datos.py",
            _t("📊 Ejecutar EDA", "📊 Run EDA", "📊 Executar EDA"),
            key="run_eda",
            heavy=False,
        )

    _show_dataset_dirs()

    st.markdown("---")

    if not EDA_DIR.exists():
        empty_state("📊", _t("EDA no disponible", "EDA not available", "EDA indisponível"),
                     _t("Ejecuta src/eda_validacion_datos.py para generar los reportes.", "Run src/eda_validacion_datos.py to generate reports.", "Execute src/eda_validacion_datos.py para gerar os relatórios."))
        return

    csv_tabs = {
        "resumen_dataset.csv": _t("Resumen del dataset", "Dataset summary", "Resumo do dataset"),
        "estadisticas_descriptivas.csv": _t("Estadísticas descriptivas", "Descriptive statistics", "Estatísticas descritivas"),
        "estadisticas_dimensiones.csv": _t("Dimensiones", "Dimensions", "Dimensões"),
        "imagenes_invalidas.csv": _t("Formatos inválidos", "Invalid formats", "Formatos inválidos"),
        "imagenes_corruptas.csv": _t("Corruptas", "Corrupted", "Corrompidas"),
        "imagenes_duplicadas.csv": _t("Duplicados", "Duplicates", "Duplicados"),
    }

    available_csvs = {name: label for name, label in csv_tabs.items() if (EDA_DIR / name).exists()}

    if available_csvs:
        tab_labels = list(available_csvs.values())
        tabs = st.tabs(tab_labels)
        for tab, (csv_name, _) in zip(tabs, available_csvs.items()):
            with tab:
                df = _read_csv(EDA_DIR / csv_name)
                if df is not None and not df.empty:
                    st.dataframe(df, use_container_width=True, hide_index=True)
                else:
                    info_box(_t("Sin datos", "No data", "Sem dados"), "info")
    else:
        info_box(_t("No se encontraron reportes CSV en reports/eda/", "No CSV reports found in reports/eda/", "Nenhum relatório CSV encontrado em reports/eda/"), "warning")

    st.markdown("---")

    png_files = sorted(EDA_DIR.glob("*.png"))
    if png_files:
        st.markdown(f"### {_t('Gráficos del EDA', 'EDA Charts', 'Gráficos do EDA')}")
        cols = st.columns(2)
        for i, img_path in enumerate(png_files):
            with cols[i % 2]:
                st.image(str(img_path), use_column_width=True, caption=img_path.stem)
    else:
        info_box(_t("No hay gráficos disponibles en reports/eda/", "No charts available in reports/eda/", "Nenhum gráfico disponível em reports/eda/"), "info")
