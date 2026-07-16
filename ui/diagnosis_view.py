"""Diagnosis view - upload, configure, analyze, and display results."""

import streamlit as st
import numpy as np
from PIL import Image
from pathlib import Path
from ui.components import section_header, confidence_bar, info_box, divider, empty_state
from database.repository import save_diagnostic, audit_log


DISEASE_CLASSES = ["Black_rot", "Esca", "Healthy", "Leaf_blight"]

DISEASE_INFO = {
    "Black_rot": {
        "name_es": "Podredumbre Negra",
        "name_en": "Black Rot",
        "name_pt": "Podridão Negra",
        "scientific": "Guignardia bidwellii",
        "desc_es": "Enfermedad fúngica que afecta bayas, hojas y brotes. Produce manchas marrones con bordes oscuros.",
        "desc_en": "Fungal disease affecting berries, leaves, and shoots. Produces brown spots with dark borders.",
        "desc_pt": "Doença fúngica que afeta bagas, folhas e brotos. Produz manchas marrons com bordas escuras.",
    },
    "Esca": {
        "name_es": "Esca (Sarampión Negro)",
        "name_en": "Esca (Black Measles)",
        "name_pt": "Esca (Sarampo Negro)",
        "scientific": "Complejo fúngico vascular",
        "desc_es": "Enfermedad de la madera que causa necrosis foliar, decaimiento y muerte progresiva de la planta.",
        "desc_en": "Wood disease causing leaf necrosis, decline, and progressive plant death.",
        "desc_pt": "Doença da madeira que causa necrose foliar, declínio e morte progressiva da planta.",
    },
    "Healthy": {
        "name_es": "Hoja Sana",
        "name_en": "Healthy Leaf",
        "name_pt": "Folha Saudável",
        "scientific": "",
        "desc_es": "La hoja no presenta signos detectables de enfermedad foliar.",
        "desc_en": "The leaf shows no detectable signs of foliar disease.",
        "desc_pt": "A folha não apresenta sinais detectáveis de doença foliar.",
    },
    "Leaf_blight": {
        "name_es": "Tizón de la Hoja",
        "name_en": "Leaf Blight",
        "name_pt": "Queima das Folhas",
        "scientific": "Pseudocercospora vitis",
        "desc_es": "Enfermedad fúngica que causa manchas irregulares de color marrón oscuro en las hojas.",
        "desc_en": "Fungal disease causing irregular dark brown spots on leaves.",
        "desc_pt": "Doença fúngica que causa manchas irregulares de cor marrom escuro nas folhas.",
    },
}


def _t(es, en, pt):
    lang = st.session_state.get("language", "es")
    return {"es": es, "en": en, "pt": pt}.get(lang, es)


def render():
    lang = st.session_state.get("language", "es")
    section_header(
        _t("Nuevo Diagnóstico", "New Diagnosis", "Novo Diagnóstico"),
        _t("Analiza una hoja de vid y obtén resultados en segundos.", "Analyze a vine leaf and get results in seconds.", "Analise uma folha de videira e obtenha resultados em segundos."),
        "scan",
    )

    uploaded_file = st.file_uploader(
        _t("Selecciona una imagen de hoja de vid", "Select a vine leaf image", "Selecione uma imagem de folha de videira"),
        type=["jpg", "jpeg", "png"],
        help=_t("Formatos soportados: JPG, JPEG, PNG", "Supported formats: JPG, JPEG, PNG", "Formatos suportados: JPG, JPEG, PNG"),
    )

    if uploaded_file is None:
        st.markdown("""
        <div style="text-align:center;padding:2rem;background:var(--bg-card);border-radius:var(--radius-lg);border:2px dashed var(--border-color);margin:1rem 0;">
            <div style="font-size:3rem;margin-bottom:0.5rem;">🍇</div>
            <h3 style="color:var(--text-primary);">{title}</h3>
            <p style="color:var(--text-secondary);">{desc}</p>
        </div>
        """.format(
            title=_t("Arrastra o selecciona una imagen", "Drag or select an image", "Arraste ou selecione uma imagem"),
            desc=_t("Formatos JPG, JPEG, PNG. Una sola hoja, bien iluminada.", "JPG, JPEG, PNG formats. Single leaf, well-lit.", "Formatos JPG, JPEG, PNG. Folha única, bem iluminada."),
        ), unsafe_allow_html=True)
        return

    image = Image.open(uploaded_file).convert("RGB")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.image(image, caption=uploaded_file.name, use_column_width=True)

    with col2:
        st.markdown(f"**{_t('Archivo', 'File', 'Arquivo')}:** {uploaded_file.name}")
        st.markdown(f"**{_t('Dimensiones', 'Dimensions', 'Dimensões')}:** {image.size[0]}x{image.size[1]} px")

        mode_opts = {
            "best": _t("Modelo recomendado (H1 - CNN + SVM)", "Recommended model (H1 - CNN + SVM)", "Modelo recomendado (H1 - CNN + SVM)"),
            "all": _t("Consenso (todos los modelos disponibles)", "Consensus (all available models)", "Consenso (todos os modelos disponíveis)"),
            "single": _t("Modelo individual", "Single model", "Modelo individual"),
        }
        mode = st.radio(
            _t("Modo de diagnóstico", "Diagnosis mode", "Modo de diagnóstico"),
            list(mode_opts.keys()),
            format_func=lambda x: mode_opts[x],
            index=0,
        )

        selected_model = "H1"
        if mode == "single":
            model_opts = {"M1": "M1 - SVM", "M2": "M2 - Random Forest", "M3": "M3 - KNN",
                          "H1": "H1 - CNN + SVM", "H2": "H2 - Transfer + RF"}
            selected_model = st.selectbox(
                _t("Selecciona modelo", "Select model", "Selecione modelo"),
                list(model_opts.keys()),
                format_func=lambda x: model_opts[x],
            )

    if st.button(_t("Analizar hoja", "Analyze leaf", "Analisar folha"), type="primary"):
        with st.spinner(_t("Analizando imagen...", "Analyzing image...", "Analisando imagem...")):
            modelos_disponibles = _get_available_models()
            if not modelos_disponibles:
                st.error(_t(
                    "No hay modelos disponibles. Carga los modelos desde la configuración.",
                    "No models available. Load models from settings.",
                    "Nenhum modelo disponível. Carregue os modelos nas configurações.",
                ))
                st.stop()

            results = []
            if mode == "best":
                if "H1" not in modelos_disponibles:
                    st.error(_t(
                        "El modelo recomendado (H1) no está disponible.",
                        "The recommended model (H1) is not available.",
                        "O modelo recomendado (H1) não está disponível.",
                    ))
                    st.stop()
                modelos_a_usar = ["H1"]
            elif mode == "single":
                if selected_model not in modelos_disponibles:
                    st.error(_t(
                        f"El modelo {selected_model} no está disponible.",
                        f"Model {selected_model} is not available.",
                        f"O modelo {selected_model} não está disponível.",
                    ))
                    st.stop()
                modelos_a_usar = [selected_model]
            else:
                modelos_a_usar = modelos_disponibles

            errores = []
            for mk in modelos_a_usar:
                display_name = MODEL_DISPLAY_NAMES.get(mk, mk)
                try:
                    result = predict_disease(image, mk, display_name)
                    results.append(result)
                except Exception as e:
                    err = str(e)
                    if "does not support image input" in err.lower():
                        err = _t(
                            "El modelo no soporta entrada de imágenes. Verifica los archivos.",
                            "Model does not support image input. Check model files.",
                            "O modelo não suporta entrada de imagens. Verifique os arquivos.",
                        )
                    errores.append((display_name, err))

            st.session_state.predictions = results
            st.session_state.prediction_mode = mode

            user = st.session_state.get("user", {})
            user_id = user.get("id", 0)
            if results and user_id:
                try:
                    top = max(results, key=lambda r: r.get("confidence", 0) or 0)
                    probs_dict = {}
                    if top.get("all_predictions") is not None:
                        for i, cls in enumerate(DISEASE_CLASSES):
                            probs_dict[cls] = float(top["all_predictions"][i])
                    save_diagnostic(
                        user_id=user_id,
                        filename=uploaded_file.name,
                        result=top["predicted_class"],
                        confidence=top.get("confidence", 0) or 0,
                        model_used=top["model_name"],
                        probabilities=probs_dict,
                        inference_time_ms=top.get("inference_time", 0),
                    )
                    audit_log(
                        user_id,
                        "diagnosis",
                        f"Diagnóstico: {top['predicted_class']} ({top.get('confidence', 0):.1%})",
                    )
                except Exception:
                    pass

    if st.session_state.get("predictions"):
        render_results()


def _get_available_models():
    model_status = st.session_state.get("model_status", {})
    return [mk for mk in MODEL_KEYS if model_status.get(mk, {}).get("disponible", False)]


def render_results():
    results = st.session_state.predictions
    lang = st.session_state.get("language", "es")

    if not results:
        st.error(_t("No se pudo obtener ninguna predicción.", "No predictions were obtained.", "Nenhuma previsão foi obtida."))
        return

    st.success(_t("Análisis completado", "Analysis completed", "Análise concluída"))

    predictions = [r["predicted_class"] for r in results]
    consensus = max(set(predictions), key=predictions.count)
    consensus_count = predictions.count(consensus)

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("### Resultado del Diagnóstico")
        disease_info = DISEASE_INFO.get(consensus, {})
        is_healthy = consensus == "Healthy"
        status_color = "var(--green-primary)" if is_healthy else "var(--red)"

        st.markdown(f"""
        <div style="
            background: {status_color}11;
            border: 1px solid {status_color}44;
            border-radius: var(--radius-lg);
            padding: 1.5rem;
            margin: 0.5rem 0;
        ">
            <div style="font-size: 1.3rem; font-weight: 700; color: {status_color};">
                {disease_info.get(f'name_{lang}', disease_info.get('name_es', consensus))}
            </div>
            {f'<div style="font-size: 0.85rem; color: var(--text-muted); font-style: italic; margin-top: 0.25rem;">{disease_info.get("scientific", "")}</div>' if disease_info.get("scientific") else ''}
            <div style="font-size: 0.9rem; color: var(--text-secondary); margin-top: 0.75rem; line-height: 1.5;">
                {disease_info.get(f'desc_{lang}', disease_info.get('desc_es', ''))}
            </div>
        </div>
        """, unsafe_allow_html=True)

        if not is_healthy:
            health_label = _t("Enfermedad detectada", "Disease detected", "Doença detectada")
            st.markdown(f"<span style='color:var(--red);font-weight:600;'>{health_label}</span>", unsafe_allow_html=True)
        else:
            health_label = _t("Hoja aparentemente sana", "Leaf appears healthy", "Folha aparentemente saudável")
            st.markdown(f"<span style='color:var(--green-primary);font-weight:600;'>{health_label}</span>", unsafe_allow_html=True)

    with col2:
        st.markdown("### Probabilidades por clase")
        best = max(results, key=lambda r: r.get("confidence", 0) or 0)
        if best.get("all_predictions") is not None:
            probs = best["all_predictions"]
            disease_names = {
                "Black_rot": _t("Podredumbre Negra", "Black Rot", "Podridão Negra"),
                "Esca": _t("Esca", "Esca", "Esca"),
                "Healthy": _t("Sana", "Healthy", "Saudável"),
                "Leaf_blight": _t("Tizón de la Hoja", "Leaf Blight", "Queima das Folhas"),
            }
            for i, cls in enumerate(DISEASE_CLASSES):
                confidence_bar(float(probs[i]), disease_names.get(cls, cls))

    if not st.session_state.get("prediction_mode") == "single" and len(results) > 1:
        st.markdown("### Consenso entre modelos")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(_t("Diagnóstico final", "Final diagnosis", "Diagnóstico final"),
                       disease_info.get(f'name_{lang}', disease_info.get('name_es', consensus)))
        with col2:
            agreement_pct = consensus_count / len(predictions) * 100
            agreement_label = _t("Alto", "High", "Alto") if agreement_pct >= 80 else _t("Medio", "Medium", "Médio") if agreement_pct >= 60 else _t("Bajo", "Low", "Baixo")
            st.metric(_t("Acuerdo", "Agreement", "Acordo"), f"{agreement_pct:.0f}% ({agreement_label})")
        with col3:
            confs = [r.get("confidence", 0) or 0 for r in results]
            avg_conf = float(np.mean(confs)) if confs else 0
            st.metric(_t("Confianza promedio", "Avg confidence", "Confiança média"), f"{avg_conf:.1%}")

        st.markdown("**Resultados individuales**")
        for r in results:
            conf = r.get("confidence", 0) or 0
            st.markdown(f"- **{r['model_name']}**: {r['predicted_class_es']} ({conf:.1%})")

    st.markdown("---")

    _render_recommendations(consensus)

    st.markdown("---")

    disclaimer = _t(
        "Este resultado es una estimación generada por inteligencia artificial y no reemplaza "
        "la evaluación de un ingeniero agrónomo o especialista fitosanitario.",
        "This result is an AI-generated estimate and does not replace the evaluation of an "
        "agronomist or phytosanitary specialist.",
        "Este resultado é uma estimativa gerada por inteligência artificial e não substitui "
        "a avaliação de um engenheiro agrônomo ou especialista fitossanitário.",
    )
    info_box(disclaimer, "warning")


def _render_recommendations(disease):
    lang = st.session_state.get("language", "es")
    recs = _get_recs(disease, lang)
    if recs:
        with st.expander(_t("Recomendaciones", "Recommendations", "Recomendações"), expanded=True):
            for item in recs:
                st.markdown(f"- {item}")


def _get_recs(disease, lang):
    all_recs = {
        "Black_rot": {
            "es": [
                "Aplicar fungicidas protectores (Mancozeb, Captan) según dosis recomendada.",
                "Eliminar y destruir partes infectadas.",
                "Mejorar circulación de aire en el viñedo.",
                "Evitar riego por aspersión en horas de alta humedad.",
                "Monitoreo semanal durante la temporada de crecimiento.",
            ],
            "en": [
                "Apply protective fungicides (Mancozeb, Captan) as recommended.",
                "Remove and destroy infected parts.",
                "Improve air circulation in the vineyard.",
                "Avoid overhead irrigation during high humidity.",
                "Weekly monitoring during growing season.",
            ],
            "pt": [
                "Aplicar fungicidas protetores (Mancozeb, Captan) conforme recomendado.",
                "Eliminar e destruir partes infectadas.",
                "Melhorar circulação de ar no vinhedo.",
                "Evitar irrigação por aspersão em alta umidade.",
                "Monitoramento semanal durante a safra.",
            ],
        },
        "Esca": {
            "es": [
                "No existe cura directa. Enfoque en prevención y manejo.",
                "Podar partes afectadas con herramientas desinfectadas.",
                "Aplicar pasta cicatrizante en cortes de poda.",
                "Considerar reemplazo de plantas severamente afectadas.",
                "Evitar podas tardías y en días húmedos.",
            ],
            "en": [
                "No direct cure available. Focus on prevention and management.",
                "Prune affected parts with disinfected tools.",
                "Apply healing paste on pruning cuts.",
                "Consider replacing severely affected plants.",
                "Avoid late pruning on humid days.",
            ],
            "pt": [
                "Não há cura direta. Foco em prevenção e manejo.",
                "Podar partes afetadas com ferramentas desinfetadas.",
                "Aplicar pasta cicatrizante em cortes de poda.",
                "Considerar substituição de plantas severamente afetadas.",
                "Evitar podas tardias em dias úmidos.",
            ],
        },
        "Leaf_blight": {
            "es": [
                "Aplicar fungicidas sistémicos (Azoxistrobina, Tebuconazol).",
                "Remover hojas infectadas y restos de poda.",
                "Mejorar el drenaje del suelo.",
                "Reducir densidad del follaje para mejorar ventilación.",
                "Evitar exceso de nitrógeno en fertilización.",
            ],
            "en": [
                "Apply systemic fungicides (Azoxystrobin, Tebuconazole).",
                "Remove infected leaves and pruning debris.",
                "Improve soil drainage.",
                "Reduce foliage density for better ventilation.",
                "Avoid excess nitrogen in fertilization.",
            ],
            "pt": [
                "Aplicar fungicidas sistêmicos (Azoxistrobina, Tebuconazol).",
                "Remover folhas infectadas e restos de poda.",
                "Melhorar drenagem do solo.",
                "Reduzir densidade da folhagem para melhor ventilação.",
                "Evitar excesso de nitrogênio na fertilização.",
            ],
        },
        "Healthy": {
            "es": [
                "No se requiere tratamiento.",
                "Mantener prácticas actuales de manejo.",
                "Continuar monitoreo regular.",
                "Mantener programa preventivo de fungicidas.",
                "Asegurar nutrición balanceada.",
            ],
            "en": [
                "No treatment required.",
                "Maintain current management practices.",
                "Continue regular monitoring.",
                "Maintain preventive fungicide program.",
                "Ensure balanced nutrition.",
            ],
            "pt": [
                "Nenhum tratamento necessário.",
                "Manter práticas atuais de manejo.",
                "Continuar monitoramento regular.",
                "Manter programa preventivo de fungicidas.",
                "Assegurar nutrição balanceada.",
            ],
        },
    }
    return all_recs.get(disease, {}).get(lang, all_recs.get(disease, {}).get("es", []))


# These are imported from app.py at runtime via st.session_state
MODEL_KEYS = ["M1", "M2", "M3", "H1", "H2"]
MODEL_DISPLAY_NAMES = {
    "M1": "M1 - SVM",
    "M2": "M2 - Random Forest",
    "M3": "M3 - KNN",
    "H1": "H1 - CNN + SVM",
    "H2": "H2 - Transfer + RF",
}


def predict_disease(image, model_key, model_display_name):
    """Wrapper for the prediction function from app.py."""
    import tempfile
    import os
    import time

    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
        image.save(tmp.name, format="JPEG")
        ruta_temp = tmp.name

    start_time = time.time()
    try:
        from predecir_imagen import predecir
        resultado = predecir(ruta_temp, model_key)
    finally:
        os.unlink(ruta_temp)
    inference_time = (time.time() - start_time) * 1000

    proba = resultado["probabilidades"]
    predicted_class = resultado["clase_predicha"]
    predicted_class_idx = DISEASE_CLASSES.index(predicted_class) if predicted_class in DISEASE_CLASSES else 0

    disease_names = {
        "Black_rot": "Podredumbre Negra",
        "Esca": "Esca (Sarampión Negro)",
        "Healthy": "Sana",
        "Leaf_blight": "Tizón de la Hoja",
    }
    predicted_class_es = disease_names.get(predicted_class, predicted_class)

    if proba is not None:
        confidence = float(proba[predicted_class_idx])
        all_predictions = np.asarray(proba, dtype=np.float64)
    else:
        confidence = None
        all_predictions = None

    return {
        "model_name": model_display_name,
        "predicted_class": predicted_class,
        "predicted_class_es": predicted_class_es,
        "confidence": confidence,
        "all_predictions": all_predictions,
        "inference_time": inference_time,
        "predicted_class_idx": predicted_class_idx,
        "probabilidades_calibradas": resultado.get("probabilidades_calibradas", False),
    }
