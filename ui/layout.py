"""Layout components: sidebar navigation, header, and page structure."""

import streamlit as st
from ui.theme import toggle_theme
from ui.components import user_avatar


NAV_ITEMS_ADMIN = [
    {"id": "dashboard", "label_es": "📊 Dashboard", "label_en": "📊 Dashboard", "label_pt": "📊 Dashboard"},
    {"id": "diagnosis", "label_es": "🔬 Nuevo Diagnóstico", "label_en": "🔬 New Diagnosis", "label_pt": "🔬 Novo Diagnóstico"},
    {"id": "history", "label_es": "📋 Historial", "label_en": "📋 History", "label_pt": "📋 Histórico"},
    {"id": "models", "label_es": "🧠 Modelos", "label_en": "🧠 Models", "label_pt": "🧠 Modelos"},
    {"id": "pipeline", "label_es": "🔧 Pipeline", "label_en": "🔧 Pipeline", "label_pt": "🔧 Pipeline"},
    {"id": "statistics", "label_es": "📈 Estadísticas", "label_en": "📈 Statistics", "label_pt": "📈 Estatísticas"},
    {"id": "reports", "label_es": "📄 Reportes", "label_en": "📄 Reports", "label_pt": "📄 Relatórios"},
]

NAV_ITEMS_CLIENT = [
    {"id": "dashboard", "label_es": "📊 Inicio", "label_en": "📊 Home", "label_pt": "📊 Início"},
    {"id": "diagnosis", "label_es": "🔬 Nuevo Diagnóstico", "label_en": "🔬 New Diagnosis", "label_pt": "🔬 Novo Diagnóstico"},
    {"id": "history", "label_es": "📋 Mi Historial", "label_en": "📋 My History", "label_pt": "📋 Meu Histórico"},
    {"id": "info", "label_es": "ℹ️ Información", "label_en": "ℹ️ Information", "label_pt": "ℹ️ Informação"},
]


def _t(es: str, en: str, pt: str) -> str:
    lang = st.session_state.get("language", "es")
    return {"es": es, "en": en, "pt": pt}.get(lang, es)


def _nav_label(item: dict) -> str:
    lang = st.session_state.get("language", "es")
    return item.get(f"label_{lang}", item["label_es"])


def render_header(page_title: str, page_subtitle: str = ""):
    user = st.session_state.get("user", {})
    name = user.get("name", "Usuario")
    role = user.get("role", "client")
    role_label = _t("Administrador", "Admin", "Administrador") if role == "admin" else _t("Cliente", "Client", "Cliente")

    col1, col2 = st.columns([2.5, 1])
    with col1:
        st.markdown(f"""
        <div style="margin-bottom: 0.5rem;">
            <h1 style="font-size: 1.5rem; font-weight: 700; margin: 0; color: var(--text-primary);">
                {page_title}
            </h1>
            {f'<p style="font-size: 0.85rem; color: var(--text-secondary); margin: 0.15rem 0 0 0;">{page_subtitle}</p>' if page_subtitle else ''}
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(
            user_avatar(name, role_label),
            unsafe_allow_html=True,
        )
    st.markdown('<hr style="margin: 0.5rem 0 1.5rem 0;">', unsafe_allow_html=True)


def render_sidebar():
    user = st.session_state.get("user", {})
    role = user.get("role", "client")
    name = user.get("name", "Usuario")
    username = st.session_state.get("username", "")
    lang = st.session_state.get("language", "es")

    with st.sidebar:
        st.markdown(f"""
        <div style="padding: 1rem 0; text-align: center;">
            <div style="font-size: 1.4rem; font-weight: 800; background: linear-gradient(135deg, var(--green-primary), var(--green-secondary));
                        -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;">
                VineGuard AI
            </div>
            <div style="font-size: 0.75rem; color: var(--text-muted); margin-top: 0.2rem;">
                {_t("Sistema de Diagnóstico", "Diagnosis System", "Sistema de Diagnóstico")}
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        nav_items = NAV_ITEMS_ADMIN if role == "admin" else NAV_ITEMS_CLIENT
        current_page = st.session_state.get("page", "dashboard")

        for item in nav_items:
            label = _nav_label(item)
            is_active = current_page == item["id"]
            if st.button(
                label,
                key=f"nav_{item['id']}",
                use_container_width=True,
                type="primary" if is_active else "secondary",
            ):
                st.session_state.page = item["id"]
                st.rerun()

        st.markdown("---")

        lang_labels = {"es": "Español", "en": "English", "pt": "Português"}
        lang_opts = {"es": "🇪🇸 Español", "en": "🇺🇸 English", "pt": "🇧🇷 Português"}
        selected_lang = st.selectbox(
            _t("Idioma", "Language", "Idioma"),
            options=list(lang_opts.keys()),
            format_func=lambda x: lang_opts[x],
            key="sidebar_lang",
            label_visibility="collapsed",
        )
        if selected_lang != lang:
            st.session_state.language = selected_lang
            st.rerun()

        dm_icon = "☀️" if st.session_state.get("dark_mode", False) else "🌙"
        dm_label = _t("Modo claro", "Light mode", "Modo claro") if st.session_state.get("dark_mode") else _t("Modo oscuro", "Dark mode", "Modo escuro")
        if st.button(f"{dm_icon} {dm_label}", key="dm_sidebar", use_container_width=True):
            toggle_theme()

        st.markdown("---")

        role_label = _t("Admin", "Admin", "Admin") if role == "admin" else _t("Cliente", "Client", "Cliente")
        st.markdown(f"""
        <div style="padding: 0.5rem 0; font-size: 0.85rem;">
            <div style="font-weight: 600; color: var(--text-primary);">{name}</div>
            <div style="color: var(--text-secondary); font-size: 0.75rem;">{role_label}</div>
        </div>
        """, unsafe_allow_html=True)

        logout_label = _t("Cerrar sesión", "Logout", "Sair")
        if st.button(logout_label, key="logout_btn", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.user = None
            st.session_state.pop("page", None)
            st.rerun()
