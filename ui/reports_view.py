"""Reports view - browse and download generated reports."""

import streamlit as st
import pandas as pd
from pathlib import Path
from ui.components import empty_state, info_box


REPORT_DIRS = {
    "EDA": Path("reports/eda"),
    "Preprocessing": Path("reports/preprocessing"),
    "Modelos": Path("reports/modelos"),
    "Estadística": Path("reports/estadistica"),
}


def _t(es: str, en: str, pt: str) -> str:
    lang = st.session_state.get("language", "es")
    return {"es": es, "en": en, "pt": pt}.get(lang, es)


def render():
    if st.button(_t("🔄 Actualizar lista de reportes", "🔄 Refresh report list", "🔄 Atualizar lista de relatórios"), key="refresh_reports"):
        st.rerun()

    tabs = st.tabs([k for k in REPORT_DIRS.keys()])

    for tab, (key, dir_path) in zip(tabs, REPORT_DIRS.items()):
        with tab:
            _render_report_dir(dir_path, key)


def _render_report_dir(dir_path: Path, label: str):
    if not dir_path.exists():
        empty_state(
            "📁",
            _t(f"No hay reportes de {label}", f"No {label} reports", f"Não há relatórios de {label}"),
            _t(f"Ejecuta los scripts correspondientes para generar reportes de {label}.", f"Run corresponding scripts to generate {label} reports.", f"Execute os scripts correspondentes para gerar relatórios de {label}."),
        )
        return

    files = []
    for ext in ["*.csv", "*.png", "*.jpg", "*.pdf", "*.json", "*.txt", "*.xlsx", "*.docx"]:
        files.extend(dir_path.rglob(ext))
    files = sorted(files)

    if not files:
        empty_state("📄", _t(f"No se encontraron archivos en {label}", f"No files found in {label}", f"Nenhum arquivo encontrado em {label}"), _t("La carpeta está vacía.", "The folder is empty.", "A pasta está vazia."))
        return

    st.markdown(f"**{len(files)} {_t('archivo(s) encontrado(s)', 'file(s) found', 'arquivo(s) encontrado(s)')}**")

    rows = []
    for f in files:
        rel = f.relative_to(Path("."))
        size_kb = f.stat().st_size / 1024
        ext = f.suffix.upper()
        rows.append({"Archivo": str(rel), "Tamaño": f"{size_kb:.1f} KB", "Tipo": ext})

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)

    st.markdown(f"### {_t('Vista previa de imágenes', 'Image preview', 'Visualização de imagens')}")
    image_files = [f for f in files if f.suffix.lower() in (".png", ".jpg", ".jpeg")]
    if image_files:
        cols = st.columns(3)
        for i, img_f in enumerate(image_files[:9]):
            with cols[i % 3]:
                st.image(str(img_f), use_column_width=True, caption=img_f.stem)
    else:
        info_box(_t("No hay imágenes para mostrar en esta categoría.", "No images to display in this category.", "Nenhuma imagem para mostrar nesta categoria."), "info")
