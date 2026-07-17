"""Layout components: sidebar navigation, header, and page structure."""

import streamlit as st
from ui.theme import toggle_theme
from ui.components import user_avatar


NAV_ITEMS = [
    {"id": "pipeline",     "label_es": "🔧 Resumen del Pipeline",     "label_en": "🔧 Pipeline Summary",     "label_pt": "🔧 Resumo do Pipeline"},
    {"id": "dataset_eda",  "label_es": "📊 Dataset y EDA",            "label_en": "📊 Dataset & EDA",          "label_pt": "📊 Dataset e EDA"},
    {"id": "preprocessing","label_es": "🔄 Preprocesamiento",          "label_en": "🔄 Preprocessing",          "label_pt": "🔄 Pré-processamento"},
    {"id": "training",    "label_es": "🧠 Entrenamiento",             "label_en": "🧠 Training",               "label_pt": "🧠 Treinamento"},
    {"id": "crossval",    "label_es": "📐 Validación Cruzada",        "label_en": "📐 Cross-Validation",       "label_pt": "📐 Validação Cruzada"},
    {"id": "hyperparams", "label_es": "⚙️ Hiperparámetros",           "label_en": "⚙️ Hyperparameters",       "label_pt": "⚙️ Hiperparâmetros"},
    {"id": "stats_tests", "label_es": "📈 Pruebas Estadísticas",      "label_en": "📈 Statistical Tests",      "label_pt": "📈 Testes Estatísticos"},
    {"id": "comparison",  "label_es": "🏆 Comparación de Modelos",    "label_en": "🏆 Model Comparison",       "label_pt": "🏆 Comparação de Modelos"},
    {"id": "best_model",  "label_es": "⭐ Mejor Modelo",              "label_en": "⭐ Best Model",             "label_pt": "⭐ Melhor Modelo"},
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
    role = user.get("role", "admin")
    role_label = _t("Admin", "Admin", "Admin") if role == "admin" else _t("Cliente", "Client", "Cliente")

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
    name = user.get("name", "Usuario")
    username = st.session_state.get("username", "")
    lang = st.session_state.get("language", "es")

    with st.sidebar:
        st.markdown(f"""
        <div style="padding: 1rem 0; text-align: center;">
            <div style="font-size: 1.4rem; font-weight: 800; background: linear-gradient(135deg, var(--green-primary), var(--green-secondary));
                        -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;">
                VineGuard AI Lab
            </div>
            <div style="font-size: 0.75rem; color: var(--text-muted); margin-top: 0.2rem;">
                {_t("Laboratorio de Machine Learning", "Machine Learning Lab", "Laboratório de Machine Learning")}
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        current_page = st.session_state.get("page", "pipeline")

        for item in NAV_ITEMS:
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

        st.markdown(f"""
        <div style="padding: 0.5rem 0; font-size: 0.85rem;">
            <div style="font-weight: 600; color: var(--text-primary);">{name}</div>
            <div style="color: var(--text-secondary); font-size: 0.75rem;">{_t("Admin", "Admin", "Admin")}</div>
        </div>
        """, unsafe_allow_html=True)

        logout_label = _t("Cerrar sesión", "Logout", "Sair")
        if st.button(logout_label, key="logout_btn", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.user = None
            st.session_state.pop("page", None)
            st.rerun()
