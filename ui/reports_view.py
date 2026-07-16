"""Reports view - browse and download generated reports."""

import streamlit as st
import pandas as pd
from pathlib import Path
from ui.components import section_header, empty_state, info_box


REPORT_DIRS = {
    "EDA": Path("reports/eda"),
    "Preprocessing": Path("reports/preprocessing"),
    "Modelos": Path("reports/modelos"),
    "Estadística": Path("reports/estadistica"),
}


def render():
    lang = st.session_state.get("language", "es")
    _t = lambda es, en, pt: {"es": es, "en": en, "pt": pt}.get(lang, es)

    section_header(
        _t("Reportes", "Reports", "Relatórios"),
        _t("Visualiza y descarga los reportes generados por el sistema", "View and download system-generated reports", "Visualize e baixe os relatórios gerados pelo sistema"),
        "📄",
    )

    tabs = st.tabs([k for k in REPORT_DIRS.keys()])

    for tab, (key, dir_path) in zip(tabs, REPORT_DIRS.items()):
        with tab:
            _render_report_dir(dir_path, key)


def _render_report_dir(dir_path: Path, label: str):
    if not dir_path.exists():
        empty_state(
            "📁",
            f"No hay reportes de {label}",
            f"Ejecuta los scripts correspondientes para generar reportes de {label}.",
        )
        return

    files = []
    for ext in ["*.csv", "*.png", "*.jpg", "*.pdf", "*.json", "*.txt", "*.xlsx", "*.docx"]:
        files.extend(dir_path.rglob(ext))
    files = sorted(files)

    if not files:
        empty_state("📄", f"No se encontraron archivos en {label}", "La carpeta está vacía.")
        return

    st.markdown(f"**{len(files)} archivo(s) encontrado(s)**")

    rows = []
    for f in files:
        rel = f.relative_to(Path("."))
        size_kb = f.stat().st_size / 1024
        ext = f.suffix.upper()
        rows.append({"Archivo": str(rel), "Tamaño": f"{size_kb:.1f} KB", "Tipo": ext})

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)

    st.markdown("### Vista previa de imágenes")
    image_files = [f for f in files if f.suffix.lower() in (".png", ".jpg", ".jpeg")]
    if image_files:
        cols = st.columns(3)
        for i, img_f in enumerate(image_files[:9]):
            with cols[i % 3]:
                st.image(str(img_f), use_column_width=True, caption=img_f.stem)
    else:
        info_box("No hay imágenes para mostrar en esta categoría.", "info")
