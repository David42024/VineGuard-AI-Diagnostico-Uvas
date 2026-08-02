"""Authentication and login page for VineGuard AI."""

import streamlit as st
from ui.theme import toggle_theme
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


LOGIN_CSS = """
<style>
/* Ocultar el header de Streamlit y el control de colapso del sidebar */
header[data-testid="stHeader"]{display:none!important;}
[data-testid="collapsedControl"]{display:none!important;}

/* Columna centrada y estrecha para toda la pantalla de login */
.main .block-container{
    max-width:460px!important;
    padding:1.75rem 1.25rem 1.5rem!important;
    margin:3vh auto 0 auto!important;
}

/* ── Contenedor sutil del formulario ──────────────────────────────────
   Se estiliza únicamente el contenedor con borde que envuelve los
   campos del login (el más interno que contiene inputs de texto). */
div[data-testid="stVerticalBlockBorderWrapper"]:has([data-testid="stTextInput"]):not(:has(div[data-testid="stVerticalBlockBorderWrapper"])){
    background:var(--bg-card)!important;
    border:1px solid var(--border-color)!important;
    border-radius:var(--radius-lg)!important;
    box-shadow:var(--shadow-md)!important;
    padding:1.75rem 1.5rem 1.25rem!important;
}

/* Etiquetas con mayor contraste */
[data-testid="stTextInput"] [data-testid="stWidgetLabel"]{
    color:var(--text-primary)!important;
    font-weight:600!important;
    font-size:0.875rem!important;
    margin-bottom:0.25rem!important;
}

/* Alturas y espaciados unificados de inputs */
[data-testid="stTextInput"] [data-baseweb="input"]{
    min-height:48px!important;
    border-radius:var(--radius-sm)!important;
    transition:border-color .2s ease, box-shadow .2s ease!important;
}
[data-testid="stTextInput"] [data-baseweb="input"]:hover{
    border-color:rgba(34,197,94,.5)!important;
}
[data-testid="stTextInput"] [data-baseweb="input"]:focus-within{
    border-color:var(--green-primary)!important;
    box-shadow:0 0 0 3px var(--green-soft)!important;
}

/* ── Fondo y texto acoplados al tema (evita texto blanco sobre fondo claro) ──
   El input interno y su contenedor deben compartir el fondo del tema y el
   texto debe heredar --text-primary (oscuro en modo claro, claro en oscuro). */
[data-testid="stTextInput"] [data-baseweb="input"],
[data-testid="stTextInput"] [data-baseweb="input"] > div,
[data-testid="stTextInput"] [data-baseweb="input"] input{
    background-color:var(--bg-input)!important;
}
[data-testid="stTextInput"] input{
    color:var(--text-primary)!important;
    -webkit-text-fill-color:var(--text-primary)!important;
    caret-color:var(--green-primary)!important;
}
[data-testid="stTextInput"] input::placeholder{
    color:var(--text-muted)!important;
    -webkit-text-fill-color:var(--text-muted)!important;
    opacity:1!important;
}

/* Autocompletado del navegador: forzar fondo y texto del tema */
[data-testid="stTextInput"] input:-webkit-autofill,
[data-testid="stTextInput"] input:-webkit-autofill:hover,
[data-testid="stTextInput"] input:-webkit-autofill:focus{
    -webkit-text-fill-color:var(--text-primary)!important;
    -webkit-box-shadow:0 0 0 1000px var(--bg-input) inset!important;
    box-shadow:0 0 0 1000px var(--bg-input) inset!important;
    caret-color:var(--green-primary)!important;
    transition:background-color 9999s ease-out 0s!important;
}

/* Íconos internos (mostrar/ocultar contraseña) según el tema */
[data-testid="stTextInput"] [data-baseweb="input"] svg{
    color:var(--text-secondary)!important;
    fill:var(--text-secondary)!important;
}
[data-testid="stTextInput"] button[aria-label="Show password"] svg,
[data-testid="stTextInput"] button[aria-label="Hide password"] svg{
    color:var(--text-secondary)!important;
    fill:var(--text-secondary)!important;
}

/* Ícono único para mostrar/ocultar contraseña: botón personalizado.
   Se ocultan los controles nativos del navegador (Edge) para que sólo
   aparezca el botón de Streamlit, alineado a la derecha y centrado. */
[data-testid="stTextInput"] input[type="password"]{
    padding-right:2.75rem!important;
}
[data-testid="stTextInput"] input[type="password"]::-ms-reveal,
[data-testid="stTextInput"] input::-ms-clear{
    display:none!important;
}
button[aria-label="Show password"],
button[aria-label="Hide password"]{
    display:flex!important;
    align-items:center!important;
    justify-content:center!important;
    position:absolute!important;
    top:50%!important;
    transform:translateY(-50%)!important;
    right:0.35rem!important;
    height:2.5rem!important;
    width:2.5rem!important;
    margin:0!important;
    padding:0!important;
    background:transparent!important;
    border:none!important;
    box-shadow:none!important;
    cursor:pointer!important;
}
button[aria-label="Show password"]:hover svg,
button[aria-label="Hide password"]:hover svg{
    color:var(--green-primary)!important;
    fill:var(--green-primary)!important;
}

/* Botón principal "Iniciar sesión": jerarquía clara */
div[data-testid="stVerticalBlockBorderWrapper"]:has([data-testid="stTextInput"]):not(:has(div[data-testid="stVerticalBlockBorderWrapper"])) .stButton > button[kind="primary"],
div[data-testid="stVerticalBlockBorderWrapper"]:has([data-testid="stTextInput"]):not(:has(div[data-testid="stVerticalBlockBorderWrapper"])) .stButton > button[data-testid="baseButton-primary"]{
    min-height:50px!important;
    font-weight:700!important;
    border-radius:var(--radius-md)!important;
    box-shadow:var(--shadow-sm)!important;
}

/* Botón secundario "Modo claro": sutil tipo ghost */
div[data-testid="stVerticalBlockBorderWrapper"]:has([data-testid="stTextInput"]):not(:has(div[data-testid="stVerticalBlockBorderWrapper"])) .stButton > button[kind="secondary"],
div[data-testid="stVerticalBlockBorderWrapper"]:has([data-testid="stTextInput"]):not(:has(div[data-testid="stVerticalBlockBorderWrapper"])) .stButton > button[data-testid="baseButton-secondary"]{
    background:transparent!important;
    border:none!important;
    color:var(--text-secondary)!important;
    min-height:40px!important;
    font-weight:500!important;
    font-size:0.85rem!important;
    margin-top:0.25rem!important;
}
div[data-testid="stVerticalBlockBorderWrapper"]:has([data-testid="stTextInput"]):not(:has(div[data-testid="stVerticalBlockBorderWrapper"])) .stButton > button[kind="secondary"]:hover,
div[data-testid="stVerticalBlockBorderWrapper"]:has([data-testid="stTextInput"]):not(:has(div[data-testid="stVerticalBlockBorderWrapper"])) .stButton > button[data-testid="baseButton-secondary"]:hover{
    background:var(--green-soft)!important;
    color:var(--green-primary)!important;
}
</style>
"""


def render_login():
    dark = st.session_state.get("dark_mode", False)
    lang = st.session_state.get("language", "es")

    st.markdown(LOGIN_CSS, unsafe_allow_html=True)

    # ── Logo + branding ──────────────────────────────────────────────────
    st.markdown(
        "<div style='text-align:center;padding:0.5rem 0 0.75rem;'>"
        "<div style='font-size:2.6rem;line-height:1.1;'>🌿</div>"
        "<div style='font-size:1.55rem;font-weight:800;color:var(--text-primary,#17201B);"
        "margin:0.35rem 0 0.2rem;'>VineGuard AI</div>"
        "<div style='font-size:0.83rem;color:var(--text-secondary,#46534C);'>"
        "Diagnóstico inteligente para la protección de cultivos de vid"
        "</div>"
        "</div>",
        unsafe_allow_html=True,
    )

    # Espaciado sutil entre el branding y la tarjeta del formulario
    st.markdown("<div style='height:0.35rem;'></div>", unsafe_allow_html=True)

    # ── Tarjeta del formulario ───────────────────────────────────────────
    with st.container(border=True):
        user_label = (
            "Usuario" if lang == "es" else "Username" if lang == "en" else "Usuário"
        )
        pass_label = (
            "Contraseña" if lang == "es" else "Password" if lang == "en" else "Senha"
        )

        username = st.text_input(user_label, placeholder="admin", key="login_username")
        password = st.text_input(
            pass_label, type="password", placeholder="••••••••", key="login_password"
        )

        # Botón principal — ancho completo y prominente
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

        # Botón de tema — secundario, sutil, debajo del principal
        dm_label = (
            ("☀️ Modo claro" if dark else "🌙 Modo oscuro") if lang == "es"
            else ("☀️ Light mode" if dark else "🌙 Dark mode") if lang == "en"
            else ("☀️ Modo claro" if dark else "🌙 Modo escuro")
        )
        if st.button(dm_label, key="dm_login_toggle", use_container_width=True):
            toggle_theme()

    # ── Pie de página ────────────────────────────────────────────────────
    st.markdown(
        "<div style='text-align:center;font-size:0.72rem;"
        "color:var(--text-muted,#7A8980);margin-top:1rem;"
        "padding-top:0.75rem;border-top:1px solid var(--border-color,#E2E8E4);'>"
        "VineGuard AI © 2026 — IA de apoyo al diagnóstico. "
        "No reemplaza la evaluación profesional."
        "</div>",
        unsafe_allow_html=True,
    )
