"""History view - per-user and global diagnosis history."""

import streamlit as st
import pandas as pd
from ui.components import section_header, empty_state, data_table, info_box
from database.repository import get_user_diagnostics, get_all_diagnostics, delete_diagnostic


def render():
    user = st.session_state.get("user", {})
    role = user.get("role", "client")
    user_id = user.get("id", 0)
    lang = st.session_state.get("language", "es")

    if role == "admin":
        section_header(
            "Historial General",
            "Todos los diagnósticos realizados en el sistema",
            "⏰",
        )
        try:
            records = get_all_diagnostics(limit=200)
        except Exception:
            records = []
    else:
        section_header(
            "Mi Historial",
            "Tus diagnósticos realizados",
            "⏰",
        )
        try:
            records = get_user_diagnostics(user_id, limit=50)
        except Exception:
            records = []

    if not records:
        empty_state(
            "📋",
            "No hay diagnósticos registrados",
            "Aún no se han realizado diagnósticos. Analiza una hoja de vid para comenzar.",
        )
        return

    df = pd.DataFrame(records)

    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"])

    search = st.text_input(
        "Buscar" if lang == "es" else "Search" if lang == "en" else "Buscar",
        placeholder="Por nombre de archivo, resultado..." if lang == "es" else "By filename, result..." if lang == "en" else "Por nome do arquivo, resultado...",
    )

    if search:
        mask = df.astype(str).apply(lambda x: x.str.contains(search, case=False, na=False)).any(axis=1)
        df = df[mask]

    cols = [c for c in ["timestamp", "filename", "result", "confidence", "model_used", "user_name"] if c in df.columns]
    if not cols:
        empty_state("📊", "Sin datos", "No hay columnas disponibles para mostrar.")
        return

    display_df = df[cols].copy()
    if "confidence" in display_df.columns:
        display_df["confidence"] = display_df["confidence"].apply(
            lambda x: f"{x:.1%}" if pd.notna(x) else "N/A"
        )
    if "timestamp" in display_df.columns:
        display_df["timestamp"] = display_df["timestamp"].dt.strftime("%Y-%m-%d %H:%M")

    # Renombrar columnas a nombres amigables
    col_labels = {
        "timestamp": "Fecha y hora",
        "user_name": "Usuario",
        "filename": "Archivo",
        "result": "Resultado",
        "confidence": "Confianza",
        "model_used": "Modelo",
    }
    display_df.rename(columns=col_labels, inplace=True)

    st.dataframe(display_df, use_container_width=True, hide_index=True)

    st.markdown("### Eliminar diagnóstico")
    diag_ids = df["id"].tolist() if "id" in df.columns else []
    if diag_ids:
        del_id = st.selectbox(
            "ID del diagnóstico a eliminar" if lang == "es" else "Diagnostic ID to delete" if lang == "en" else "ID do diagnóstico para excluir",
            diag_ids,
        )
        if st.button("Eliminar" if lang == "es" else "Delete" if lang == "en" else "Excluir", type="secondary"):
            try:
                if role == "admin":
                    delete_diagnostic(del_id)
                else:
                    delete_diagnostic(del_id, user_id)
                info_box("Diagnóstico eliminado." if lang == "es" else "Diagnostic deleted." if lang == "en" else "Diagnóstico excluído.", "success")
                st.rerun()
            except Exception as e:
                info_box(f"Error: {e}", "error")
