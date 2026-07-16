"""Reusable UI components for VineGuard AI — native Streamlit only."""

import streamlit as st
import pandas as pd


def metric_card(icon: str, title: str, value, subtitle: str = "",
                color: str = "green", help_text: str = ""):
    """Metric card usando st.metric() nativo de Streamlit (sin HTML)."""
    label = f"{icon} {title}" if icon else title
    val = str(value) if value is not None else "N/A"
    st.metric(label=label, value=val, help=subtitle if subtitle else None)


def status_badge(status: str, text: str = "") -> str:
    """Devuelve emoji + texto. Sin HTML para evitar renderizado roto."""
    icons = {
        "completed":  "✅",
        "running":    "🔵",
        "pending":    "⬜",
        "error":      "❌",
        "healthy":    "🟢",
        "diseased":   "🔴",
        "warning":    "⚠️",
        "loaded":     "✅",
        "not_loaded": "❌",
    }
    label = text or status.replace("_", " ").capitalize()
    return f"{icons.get(status, '⚪')} {label}"


def section_header(title: str, subtitle: str = "", icon: str = ""):
    """Encabezado de sección usando markdown nativo."""
    prefix = f"{icon} " if icon else ""
    st.markdown(f"## {prefix}{title}")
    if subtitle:
        st.caption(subtitle)


def divider():
    st.divider()


def empty_state(icon: str, title: str, description: str,
                action_label: str = "", action_key: str = ""):
    """Estado vacío usando st.info() nativo."""
    st.info(f"{icon} **{title}** — {description}")
    if action_label and action_key:
        st.button(action_label, key=action_key, type="primary")


def info_box(message: str, type_: str = "info"):
    """Caja de mensaje usando widgets nativos de Streamlit."""
    if type_ == "success":
        st.success(message)
    elif type_ == "warning":
        st.warning(message)
    elif type_ == "error":
        st.error(message)
    else:
        st.info(message)


def data_table(df: pd.DataFrame, pagination: bool = True, page_size: int = 10):
    if df.empty:
        return
    st.dataframe(df, use_container_width=True, hide_index=True)


def confidence_bar(confidence: float, label: str = ""):
    """Barra de confianza usando st.progress() nativo."""
    if confidence is None:
        return
    pct = min(1.0, max(0.0, float(confidence)))
    if label:
        st.caption(label)
    st.progress(pct, text=f"{pct * 100:.1f}%")


def model_card(model_name: str, model_type: str, metrics: dict,
               status: str = "loaded", is_best: bool = False):
    """Tarjeta de modelo con HTML en una sola línea por atributo."""
    badge = status_badge(status)
    best = " ⭐" if is_best else ""
    border = "2px solid #22C55E" if is_best else "1px solid #E2E8E4"
    rows = "".join(
        f'<div style="font-size:0.82rem;">{k}: <strong>{v}</strong></div>'
        for k, v in metrics.items() if v is not None
    )
    html = (
        f'<div style="background:#fff;border:{border};border-radius:12px;padding:1rem;margin:0.5rem 0;">'
        f'<div style="display:flex;justify-content:space-between;">'
        f'<strong>{model_name}{best}</strong>'
        f'<span style="font-size:0.75rem;color:#6B7280;">{model_type}</span>'
        f'</div>'
        f'<div style="margin:0.4rem 0;">{badge}</div>'
        f'{rows}'
        f'</div>'
    )
    return html


def user_avatar(name: str, role: str) -> str:
    """Avatar de usuario — HTML en línea única por atributo."""
    initials = "".join(w[0].upper() for w in name.split()[:2])
    return (
        '<div style="display:flex;align-items:center;gap:0.75rem;">'
        f'<div style="width:36px;height:36px;border-radius:50%;background:linear-gradient(135deg,#166534,#22C55E);'
        f'display:flex;align-items:center;justify-content:center;color:white;font-weight:700;font-size:0.85rem;">'
        f'{initials}</div>'
        f'<div>'
        f'<div style="font-size:0.9rem;font-weight:600;">{name}</div>'
        f'<div style="font-size:0.75rem;color:#6B7280;">{role}</div>'
        f'</div>'
        f'</div>'
    )


def stepper(steps: list):
    """Stepper usando componentes nativos de Streamlit. Sin HTML."""
    icons_map = {
        "completed": "✅",
        "running":   "🔵",
        "pending":   "⬜",
        "error":     "❌",
    }
    for step in steps:
        icon = icons_map.get(step.get("status", "pending"), "⬜")
        st.markdown(f"{icon} **{step['label']}**")
        if step.get("detail"):
            st.caption(step["detail"])
