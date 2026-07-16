"""Preprocessing view — shows augmentation config and visual examples."""

import streamlit as st
from pathlib import Path
from ui.components import section_header, info_box, empty_state, run_script_button


PREPROCESSING_DIR = Path("reports/preprocessing")


def _t(es: str, en: str, pt: str) -> str:
    lang = st.session_state.get("language", "es")
    return {"es": es, "en": en, "pt": pt}.get(lang, es)


def _show_config():
    try:
        from mantenedor import IMG_SIZE, TARGET_TRAIN_SAMPLES_PER_CLASS
    except ImportError:
        IMG_SIZE = (224, 224)
        TARGET_TRAIN_SAMPLES_PER_CLASS = 1500

    st.markdown(f"### {_t('Configuración', 'Configuration', 'Configuração')}")
    cols = st.columns(3)
    with cols[0]:
        st.metric(_t("Redimensionamiento", "Resize", "Redimensionamento"), f"{IMG_SIZE[0]}×{IMG_SIZE[1]}")
    with cols[1]:
        st.metric(_t("Normalización", "Normalization", "Normalização"), "pixel / 255")
    with cols[2]:
        st.metric(_t("Target de balanceo", "Balancing target", "Alvo de balanceamento"), f"{TARGET_TRAIN_SAMPLES_PER_CLASS}")

    st.markdown(f"### {_t('Técnicas de aumento', 'Augmentation techniques', 'Técnicas de aumento')}")
    techs = {
        "Rotación": "±30°",
        "Brillo": "factor 0.6–1.4",
        "Zoom": "0.85–1.15",
        "Contraste": "factor 0.6–1.4",
        "Desplazamiento": "10% máximo",
        "Volteo horizontal": "50% probabilidad",
    }
    cols = st.columns(3)
    for i, (name, detail) in enumerate(techs.items()):
        with cols[i % 3]:
            st.info(f"**{name}**  \n{detail}")


def render():
    lang = st.session_state.get("language", "es")
    section_header(
        _t("Preprocesamiento y Aumento", "Preprocessing & Augmentation", "Pré-processamento e Aumento"),
        _t("Configuración y ejemplos visuales del preprocesamiento", "Configuration and visual examples of preprocessing", "Configuração e exemplos visuais do pré-processamento"),
        "🔄",
    )

    run_script_button(
        "src/preprocesamiento_aumento.py",
        _t("🔄 Ejecutar preprocesamiento", "🔄 Run preprocessing", "🔄 Executar pré-processamento"),
        key="run_preprocessing",
        heavy=False,
    )

    _show_config()

    st.markdown("---")

    if not PREPROCESSING_DIR.exists():
        empty_state("🔄", _t("Sin ejemplos", "No examples", "Sem exemplos"),
                     _t("Ejecuta src/preprocesamiento_aumento.py para generar los ejemplos visuales.", "Run src/preprocesamiento_aumento.py to generate visual examples.", "Execute src/preprocesamiento_aumento.py para gerar exemplos visuais."))
        return

    png_files = sorted(PREPROCESSING_DIR.glob("*.png"))
    if png_files:
        st.markdown(f"### {_t('Ejemplos visuales', 'Visual examples', 'Exemplos visuais')}")
        cols = st.columns(2)
        for i, img_path in enumerate(png_files):
            with cols[i % 2]:
                st.image(str(img_path), use_column_width=True, caption=img_path.stem)
    else:
        info_box(_t("No hay imágenes en reports/preprocessing/", "No images in reports/preprocessing/", "Nenhuma imagem em reports/preprocessing/"), "info")
