"""Reusable UI components for VineGuard AI — native Streamlit only."""

import os
import subprocess
import sys
import streamlit as st
import pandas as pd
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
MAX_LINES = 50


def _stream_output(process: subprocess.Popen, output_box) -> list[str]:
    """Lee stdout línea por línea y actualiza output_box con las últimas MAX_LINES."""
    lineas: list[str] = []
    if process.stdout is None:
        return lineas
    for raw in iter(process.stdout.readline, ""):
        linea = raw.rstrip()
        if not linea:
            continue
        lineas.append(linea)
        output_box.code("\n".join(lineas[-MAX_LINES:]), language="text")
    return lineas


def run_script_button(
    script_name: str,
    button_label: str,
    *,
    confirm_message: str = "",
    key: str = "",
    heavy: bool = True,
    reload_callback=None,
    on_start=None,
) -> bool:
    """Botón que ejecuta un script Python con subprocess.Popen y salida progresiva.

    Args:
        script_name: Ruta relativa al script (ej. 'src/eda_validacion_datos.py')
        button_label: Texto del botón
        confirm_message: Mensaje de confirmación (vacío = sin confirmación)
        key: Key única para el botón y estado
        heavy: Si True, pide confirmación al usuario antes de ejecutar
        reload_callback: Función a llamar tras éxito (para recargar datos)

    Returns:
        True si el script se ejecutó con éxito, False en otro caso.
    """
    running_key = f"_running_{key or script_name}"
    is_running = st.session_state.get(running_key, False)

    # Deshabilitar botones mientras corre cualquier proceso
    any_running = any(
        v for k, v in st.session_state.items()
        if k.startswith("_running_") and v
    )

    if st.button(
        button_label,
        key=key or f"btn_{script_name}",
        disabled=any_running,
        use_container_width=True,
        type="primary" if not any_running else "secondary",
    ):
        if heavy and confirm_message:
            st.session_state[f"_confirm_{key or script_name}"] = True
        else:
            if on_start:
                on_start()
            st.session_state[running_key] = True
            st.rerun()

    # Confirmación
    confirm_key = f"_confirm_{key or script_name}"
    if st.session_state.get(confirm_key, False):
        with st.expander("⚠️ Confirmar ejecución", expanded=True):
            st.warning(confirm_message)
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Ejecutar", key=f"{key}_yes", type="primary"):
                    st.session_state[confirm_key] = False
                    if on_start:
                        on_start()
                    st.session_state[running_key] = True
                    st.rerun()
            with col2:
                if st.button("❌ Cancelar", key=f"{key}_no"):
                    st.session_state[confirm_key] = False
                    st.rerun()

    # Ejecución con salida progresiva
    if is_running:
        script_path = BASE_DIR / script_name
        cmd_display = f"{sys.executable} {script_name}"

        with st.status(
            f"⏳ Iniciando **{button_label}**...",
            expanded=True,
        ) as status:
            st.code(cmd_display, language="bash")
            output_box = st.empty()

            try:
                process = subprocess.Popen(
                    [sys.executable, str(script_path)],
                    cwd=str(BASE_DIR),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    bufsize=1,
                    env={**os.environ, "PYTHONUNBUFFERED": "1", "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"},
                )

                lineas = _stream_output(process, output_box)
                return_code = process.wait()

                if return_code == 0:
                    status.update(
                        label=f"✅ {button_label} completado",
                        state="complete",
                        expanded=False,
                    )
                    st.success(f"{button_label} finalizado correctamente.")
                    st.session_state[running_key] = False
                    if reload_callback:
                        reload_callback()
                    st.rerun()
                    return True
                else:
                    status.update(
                        label=f"❌ {button_label} — Error (código {return_code})",
                        state="error",
                        expanded=True,
                    )
                    st.error(f"El proceso terminó con código {return_code}.")
                    st.session_state[running_key] = False
                    return False

            except FileNotFoundError:
                status.update(label=f"❌ Script no encontrado", state="error")
                st.error(f"No se encontró: `{script_path}`")
                st.session_state[running_key] = False
                return False
            except Exception as e:
                status.update(label=f"❌ Error inesperado", state="error")
                st.error(f"{type(e).__name__}: {e}")
                st.session_state[running_key] = False
                return False

    return False


def reload_ranking_callback():
    """Recarga ranking_data y best_model_name en session_state tras ejecutar scripts."""
    import pandas as pd
    ranking_path = BASE_DIR / "reports" / "modelos" / "ranking_modelos.csv"
    best_path = BASE_DIR / "reports" / "modelos" / "mejor_modelo.txt"
    try:
        if ranking_path.exists():
            df = pd.read_csv(ranking_path)
            st.session_state.ranking_data = df.to_dict("records")
        if best_path.exists():
            with open(best_path, encoding="utf-8") as f:
                st.session_state.best_model_name = f.read().strip()
    except Exception:
        pass


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
