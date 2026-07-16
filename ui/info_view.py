"""Educational information view for clients."""

import streamlit as st
from ui.components import section_header, info_box


def render():
    lang = st.session_state.get("language", "es")
    _t = lambda es, en, pt: {"es": es, "en": en, "pt": pt}.get(lang, es)

    section_header(
        _t("Información del Sistema", "System Information", "Informação do Sistema"),
        _t("Cómo funciona VineGuard AI", "How VineGuard AI works", "Como funciona o VineGuard AI"),
        "info",
    )

    with st.expander(_t("Enfermedades Reconocidas", "Recognized Diseases", "Doenças Reconhecidas"), expanded=True):
        st.markdown(f"""
        - **{_t("Podredumbre Negra", "Black Rot", "Podridão Negra")}** - {_t("Causada por Guignardia bidwellii. Afecta bayas, hojas y brotes.", "Caused by Guignardia bidwellii. Affects berries, leaves, and shoots.", "Causada por Guignardia bidwellii. Afeta bagas, folhas e brotos.")}
        - **{_t("Esca", "Esca", "Esca")}** - {_t("Complejo de hongos vasculares. Enfermedad de la madera.", "Vascular fungi complex. Wood disease.", "Complexo de fungos vasculares. Doença da madeira.")}
        - **{_t("Tizón de la Hoja", "Leaf Blight", "Queima das Folhas")}** - {_t("Causada por Pseudocercospora vitis. Manchas irregulares oscuras.", "Caused by Pseudocercospora vitis. Irregular dark spots.", "Causada por Pseudocercospora vitis. Manchas escuras irregulares.")}
        - **{_t("Hoja Sana", "Healthy Leaf", "Folha Saudável")}** - {_t("Sin signos detectables de enfermedad.", "No detectable signs of disease.", "Sem sinais detectáveis de doença.")}
        """)

    with st.expander(_t("Cómo tomar una buena fotografía", "How to take a good photo", "Como tirar uma boa foto")):
        tips_es = "1. Utiliza una hoja completa y en buen estado.\n2. Buena iluminación, preferiblemente luz natural.\n3. Evita imágenes borrosas o desenfocadas.\n4. Centra la hoja, que ocupe al menos el 70% del encuadre.\n5. Fondo simple y uniforme.\n6. Evita sombras y reflejos.\n7. Resolución mínima recomendada: 500x500 píxeles."
        tips_en = "1. Use a complete leaf in good condition.\n2. Good lighting, preferably natural light.\n3. Avoid blurry or out-of-focus images.\n4. Center the leaf, occupying at least 70% of the frame.\n5. Simple, uniform background.\n6. Avoid shadows and reflections.\n7. Minimum recommended resolution: 500x500 pixels."
        tips_pt = "1. Use uma folha completa em boas condições.\n2. Boa iluminação, de preferência luz natural.\n3. Evite imagens borradas ou desfocadas.\n4. Centralize a folha, ocupando pelo menos 70% do enquadramento.\n5. Fundo simples e uniforme.\n6. Evite sombras e reflexos.\n7. Resolução mínima recomendada: 500x500 píxeles."
        st.markdown(f"\n{_t(tips_es, tips_en, tips_pt)}\n")

    with st.expander(_t("Cómo funciona la IA", "How the AI works", "Como a IA funciona")):
        ai_es = (
            "VineGuard AI utiliza redes neuronales convolucionales (CNN) y modelos de machine learning "
            "para analizar imágenes de hojas de vid. El sistema:\n\n"
            "1. Recibe una imagen y la preprocesa (redimensiona, normaliza).\n"
            "2. Extrae características visuales mediante modelos entrenados.\n"
            "3. Compara las características con patrones de enfermedades conocidas.\n"
            "4. Genera una predicción con nivel de confianza.\n"
            "5. Si se usa consenso, combina resultados de múltiples modelos.\n\n"
            "Los modelos fueron entrenados con miles de imágenes etiquetadas por expertos."
        )
        ai_en = (
            "VineGuard AI uses convolutional neural networks (CNN) and machine learning models "
            "to analyze grapevine leaf images. The system:\n\n"
            "1. Receives an image and preprocesses it (resize, normalize).\n"
            "2. Extracts visual features using trained models.\n"
            "3. Compares features with known disease patterns.\n"
            "4. Generates a prediction with confidence level.\n"
            "5. If consensus mode, combines results from multiple models.\n\n"
            "Models were trained with thousands of images labeled by experts."
        )
        ai_pt = (
            "O VineGuard AI usa redes neurais convolucionais (CNN) e modelos de machine learning "
            "para analisar imagens de folhas de videira. O sistema:\n\n"
            "1. Recebe uma imagem e a pré-processa (redimensiona, normaliza).\n"
            "2. Extrai características visuais usando modelos treinados.\n"
            "3. Compara as características com padrões de doenças conhecidas.\n"
            "4. Gera uma previsão com nível de confiança.\n"
            "5. Se usar consenso, combina resultados de vários modelos.\n\n"
            "Os modelos foram treinados com milhares de imagens rotuladas por especialistas."
        )
        st.markdown(f"\n{_t(ai_es, ai_en, ai_pt)}\n")

    with st.expander(_t("Limitaciones del Sistema", "System Limitations", "Limitações do Sistema")):
        lim_es = (
            "- El diagnóstico es una estimación basada en inteligencia artificial.\n"
            "- No reemplaza la evaluación de un especialista fitosanitario.\n"
            "- La precisión depende de la calidad de la imagen proporcionada.\n"
            "- Algunas enfermedades pueden no ser detectadas en etapas tempranas.\n"
            "- El sistema está limitado a las clases de enfermedades para las que fue entrenado.\n"
            "- Factores ambientales y daños mecánicos pueden generar falsos positivos."
        )
        lim_en = (
            "- The diagnosis is an AI-based estimate.\n"
            "- It does not replace evaluation by a phytosanitary specialist.\n"
            "- Accuracy depends on the quality of the provided image.\n"
            "- Some diseases may not be detected in early stages.\n"
            "- The system is limited to disease classes it was trained on.\n"
            "- Environmental factors and mechanical damage may cause false positives."
        )
        lim_pt = (
            "- O diagnóstico é uma estimativa baseada em inteligência artificial.\n"
            "- Não substitui a avaliação de um especialista fitossanitário.\n"
            "- A precisão depende da qualidade da imagem fornecida.\n"
            "- Algumas doenças podem não ser detectadas em estágios iniciais.\n"
            "- O sistema está limitado às classes de doenças para as quais foi treinado.\n"
            "- Fatores ambientais e danos mecânicos podem gerar falsos positivos."
        )
        st.markdown(f"\n{_t(lim_es, lim_en, lim_pt)}\n")

    with st.expander(_t("Uso Responsable", "Responsible Use", "Uso Responsável")):
        info_box(
            _t(
                "Este sistema es una herramienta de apoyo al diagnóstico. Las decisiones de manejo "
                "fitosanitario deben ser tomadas por profesionales calificados basándose en "
                "evaluaciones de campo completas.",
                "This system is a diagnostic support tool. Phytosanitary management decisions "
                "should be made by qualified professionals based on complete field evaluations.",
                "Este sistema é uma ferramenta de apoio ao diagnóstico. As decisões de manejo "
                "fitossanitário devem ser tomadas por profissionais qualificados com base em "
                "avaliações de campo completas.",
            ),
            "warning",
        )

    if st.session_state.get("ranking_data"):
        st.markdown("### Ranking de Modelos")
        import pandas as pd
        df = pd.DataFrame(st.session_state.ranking_data)
        display_cols = [c for c in ["modelo", "accuracy", "f1_score", "mcc"] if c in df.columns]
        if display_cols:
            st.dataframe(df[display_cols].head(10), use_container_width=True, hide_index=True)
