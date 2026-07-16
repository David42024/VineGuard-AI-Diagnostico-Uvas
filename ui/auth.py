"""Authentication and login page for VineGuard AI."""

import streamlit as st
from ui.theme import toggle_theme
from ui.components import info_box
from database.repository import authenticate, init_database


def init_auth():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "user" not in st.session_state:
        st.session_state.user = None
    try:
        init_database()
    except Exception:
        pass


def render_login():
    dark = st.session_state.get("dark_mode", False)
    lang = st.session_state.get("language", "es")

    # ── CSS: card centrada, header oculto ──────────────────────────────────
    # Todo en una sola línea por propiedad → sin atributos multilínea
    st.markdown(
        "<style>"
        "header[data-testid='stHeader']{display:none!important;}"
        "[data-testid='collapsedControl']{display:none!important;}"
        ".main .block-container{"
        "max-width:480px!important;"
        "padding:2.5rem 2rem 1.5rem!important;"
        "margin:4vh auto 0 auto!important;"
        "border-radius:16px!important;"
        "box-shadow:0 4px 24px rgba(0,0,0,0.09)!important;"
        "}"
        "</style>",
        unsafe_allow_html=True,
    )

    # ── Logo + branding (bloque HTML único, auto-contenido) ────────────────
    st.markdown(
        "<div style='text-align:center;padding:0.25rem 0 1rem;'>"
        "<div style='font-size:2.6rem;line-height:1.1;'>🌿</div>"
        "<div style='font-size:1.55rem;font-weight:800;color:var(--text-primary,#17201B);"
        "margin:0.35rem 0 0.2rem;'>VineGuard AI</div>"
        "<div style='font-size:0.83rem;color:var(--text-secondary,#647067);'>"
        "Diagnóstico inteligente para la protección de cultivos de vid"
        "</div>"
        "</div>",
        unsafe_allow_html=True,
    )

    st.divider()

    # ── Selector de idioma (único) ─────────────────────────────────────────
    lang_opts = {"es": "🇪🇸 Español", "en": "🇺🇸 English", "pt": "🇧🇷 Português"}
    selected = st.selectbox(
        "Idioma",
        options=list(lang_opts.keys()),
        format_func=lambda x: lang_opts[x],
        key="login_lang",
        label_visibility="collapsed",
    )
    if selected != lang:
        st.session_state.language = selected
        st.rerun()

    # ── Campos del formulario ──────────────────────────────────────────────
    user_label = "Usuario" if lang == "es" else "Username" if lang == "en" else "Usuário"
    pass_label = "Contraseña" if lang == "es" else "Password" if lang == "en" else "Senha"

    username = st.text_input(user_label, placeholder="admin", key="login_username")
    password = st.text_input(
        pass_label, type="password", placeholder="••••••••", key="login_password"
    )

    # ── Botón principal — ancho completo ───────────────────────────────────
    login_label = (
        "Iniciar sesión" if lang == "es"
        else "Sign in" if lang == "en"
        else "Entrar"
    )
    if st.button(login_label, type="primary", use_container_width=True, key="login_btn"):
        if not username or not password:
            err = (
                "Ingresa usuario y contraseña" if lang == "es"
                else "Enter username and password" if lang == "en"
                else "Insira usuário e senha"
            )
            st.error(err)
        else:
            spin_msg = (
                "Verificando credenciales…" if lang == "es"
                else "Verifying credentials…" if lang == "en"
                else "Verificando credenciais…"
            )
            with st.spinner(spin_msg):
                user = authenticate(username, password)
                if user:
                    st.session_state.logged_in = True
                    st.session_state.user = user
                    st.session_state.username = user["username"]
                    st.rerun()
                else:
                    err = (
                        "Usuario o contraseña incorrectos" if lang == "es"
                        else "Incorrect username or password" if lang == "en"
                        else "Usuário ou senha incorretos"
                    )
                    st.error(err)

    # ── Botón de tema — secundario, debajo del principal ───────────────────
    dm_label = (
        ("☀️ Modo claro" if dark else "🌙 Modo oscuro") if lang == "es"
        else ("☀️ Light mode" if dark else "🌙 Dark mode") if lang == "en"
        else ("☀️ Modo claro" if dark else "🌙 Modo escuro")
    )
    if st.button(dm_label, key="dm_login_toggle", use_container_width=True):
        toggle_theme()

    # ── Pie de página (bloque HTML único, auto-contenido) ──────────────────
    st.markdown(
        "<div style='text-align:center;font-size:0.72rem;"
        "color:var(--text-muted,#94A39A);margin-top:1rem;"
        "padding-top:0.75rem;border-top:1px solid var(--border-color,#E2E8E4);'>"
        "VineGuard AI © 2026 — IA de apoyo al diagnóstico. "
        "No reemplaza la evaluación profesional."
        "</div>",
        unsafe_allow_html=True,
    )
