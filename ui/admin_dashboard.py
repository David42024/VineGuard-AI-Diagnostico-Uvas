"""Admin dashboard view — native Streamlit, sin HTML custom en las métricas."""

import streamlit as st
import pandas as pd
from ui.components import section_header, empty_state, data_table
from database.repository import get_admin_stats, get_disease_distribution

# Columnas internas → nombres amigables
_COL_LABELS = {
    "timestamp":  "Fecha y hora",
    "user_name":  "Usuario",
    "filename":   "Archivo",
    "result":     "Resultado",
    "confidence": "Confianza",
    "model_used": "Modelo",
}


def render():
    section_header(
        "Panel de Administración",
        "Resumen ejecutivo del sistema de diagnóstico",
        "📊",
    )

    # ── Obtener estadísticas ────────────────────────────────────────────────
    stats = {}
    try:
        stats = get_admin_stats()
    except Exception:
        pass

    ranking_data = st.session_state.get("ranking_data", []) or []
    best_model_raw = st.session_state.get("best_model_name", "") or ""
    best_model = (
        best_model_raw.split(":", 1)[1].strip()
        if ":" in best_model_raw
        else (best_model_raw or "N/A")
    )

    # ── Cuatro métricas principales — st.metric nativo ─────────────────────
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📄 Total Diagnósticos", stats.get("total_diagnostics", 0))
    with col2:
        st.metric("📅 Diagnósticos Hoy", stats.get("today_diagnostics", 0))
    with col3:
        st.metric("💚 Hojas Sanas", f"{stats.get('healthy_pct', 0):.1f}%")
    with col4:
        st.metric("🎯 Mejor Modelo", best_model or "N/A")

    # ── Detalle del mejor modelo ────────────────────────────────────────────
    if ranking_data:
        with st.expander("📋 Detalle del mejor modelo", expanded=False):
            top = pd.DataFrame(ranking_data).iloc[0] if ranking_data else None
            if top is not None:
                c1, c2, c3 = st.columns(3)
                with c1:
                    acc = top.get("accuracy")
                    st.metric("Accuracy", f"{float(acc)*100:.2f}%" if acc is not None else "N/A")
                with c2:
                    f1 = top.get("f1_score")
                    st.metric("F1-macro", f"{float(f1)*100:.2f}%" if f1 is not None else "N/A")
                with c3:
                    mcc = top.get("mcc")
                    st.metric("MCC", f"{float(mcc)*100:.2f}%" if mcc is not None else "N/A")
                st.caption(
                    "Criterio: mayor MCC ponderado con Accuracy y F1-macro "
                    "para garantizar robustez ante clases desbalanceadas."
                )

    # ── Distribución + Ranking ──────────────────────────────────────────────
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Distribución de Enfermedades")
        try:
            dist = get_disease_distribution()
            if dist:
                df_dist = pd.DataFrame(list(dist.items()), columns=["Diagnóstico", "Cantidad"])
                st.dataframe(df_dist, use_container_width=True, hide_index=True)
            else:
                empty_state("📊", "Sin datos", "No hay diagnósticos registrados aún.")
        except Exception:
            empty_state("📊", "Sin datos", "No hay diagnósticos registrados aún.")

    with col2:
        st.markdown("### Ranking de Modelos")
        if ranking_data:
            df_rank = pd.DataFrame(ranking_data)
            display_cols = [c for c in ["modelo", "accuracy", "f1_score", "mcc"]
                            if c in df_rank.columns]
            if display_cols:
                st.dataframe(df_rank[display_cols].head(10), use_container_width=True,
                             hide_index=True)
        else:
            empty_state("🧠", "Sin datos",
                        "No hay ranking disponible. Ejecuta la selección de modelo.")

    # ── Últimos diagnósticos ────────────────────────────────────────────────
    st.markdown("### Últimos Diagnósticos")
    try:
        from database.repository import get_all_diagnostics
        recent = get_all_diagnostics(limit=10)
        if recent:
            df_recent = pd.DataFrame(recent)
            cols_order = [c for c in ["timestamp", "user_name", "filename",
                                       "result", "confidence", "model_used"]
                          if c in df_recent.columns]
            if cols_order:
                display = df_recent[cols_order].copy()
                if "confidence" in display.columns:
                    display["confidence"] = display["confidence"].apply(
                        lambda x: f"{float(x)*100:.2f}%" if x is not None and x != "" else "N/A"
                    )
                if "timestamp" in display.columns:
                    display["timestamp"] = pd.to_datetime(
                        display["timestamp"], errors="coerce"
                    ).dt.strftime("%Y-%m-%d %H:%M")
                display.rename(columns=_COL_LABELS, inplace=True)
                st.dataframe(display, use_container_width=True, hide_index=True)
        else:
            empty_state("⏰", "Sin actividad", "No hay diagnósticos recientes.")
    except Exception:
        empty_state("⏰", "Sin datos", "No hay diagnósticos registrados.")
