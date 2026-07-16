"""Client dashboard - simplified home view for regular users."""

import streamlit as st
from ui.components import section_header, metric_card, empty_state, info_box
from database.repository import get_user_stats


def render():
    user = st.session_state.get("user", {})
    user_id = user.get("id", 0)
    name = user.get("name", "Usuario")
    lang = st.session_state.get("language", "es")

    greeting = "Bienvenido" if lang == "es" else "Welcome" if lang == "en" else "Bem-vindo"
    section_header(
        f"{greeting}, {name}",
        "Analiza una hoja de vid en pocos segundos y obtén un diagnóstico preciso.",
        "🏠",
    )

    stats = {"total": 0, "healthy": 0, "diseased": 0, "today": 0, "last_diagnosis": None}
    try:
        if user_id:
            stats = get_user_stats(user_id)
    except Exception:
        pass

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        metric_card("📋", "Total Análisis", stats["total"], color="green")
    with col2:
        metric_card("✅", "Hojas Sanas", stats["healthy"], color="green")
    with col3:
        metric_card("⚠️", "Hojas Enfermas", stats["diseased"], color="red")
    with col4:
        metric_card("⏰", "Análisis Hoy", stats["today"], color="blue")

    st.markdown("### Realizar nuevo diagnóstico")
    info_box(
        "Sube una foto de una hoja de vid para obtener un diagnóstico automático "
        "utilizando inteligencia artificial. El análisis tarda solo unos segundos.",
        "info",
    )

    new_label = "Realizar nuevo diagnóstico" if lang == "es" else "New diagnosis" if lang == "en" else "Novo diagnóstico"
    if st.button(new_label, type="primary", key="new_diag_btn"):
        st.session_state.page = "diagnosis"
        st.rerun()

    if stats.get("last_diagnosis"):
        st.markdown("### Último diagnóstico")
        last = stats["last_diagnosis"]
        col1, col2 = st.columns(2)
        with col1:
            metric_card("🔍", "Resultado", last.get("result", "N/A"),
                        color="green" if last.get("result") == "Healthy" else "red")
        with col2:
            conf = last.get("confidence", 0)
            metric_card("📊", "Confianza", f"{conf:.1%}" if conf else "N/A",
                        color="green" if conf and conf >= 0.7 else "amber")
    else:
        empty_state(
            "🔍",
            "Aún no tienes diagnósticos",
            "Analiza tu primera hoja de vid para comenzar.",
        )

    st.markdown("### Recomendaciones para capturar una buena imagen")
    recs = [
        "Utiliza una hoja completa y en buen estado.",
        "Mantén buena iluminación, evita sombras y reflejos.",
        "Evita imágenes borrosas o con movimiento.",
        "Centra la hoja en la imagen, evita fondos complejos.",
        "La hoja debe ocupar al menos el 70% del encuadre.",
    ]
    for r in recs:
        st.markdown(f"- {r}")
