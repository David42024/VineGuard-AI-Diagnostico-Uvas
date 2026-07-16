# VineGuard AI — Sistema de Diagnóstico de Enfermedades en Hojas de Uva

[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](#)
[![License: MIT](https://img.shields.io/badge/License-MIT-green)](#)
[![Streamlit](https://img.shields.io/badge/Streamlit-App-orange)](#)

**VineGuard AI** es una plataforma de inteligencia artificial para la detección temprana y precisa de enfermedades foliares en vid. Implementa **modelos clásicos**, **modelos híbridos** y **redes neuronales profundas (CNN)** con validación estadística robusta (McNemar, Matthews, Bootstrap).

---

## Características

- **5 modelos integrados** en pipeline: SVM, Random Forest, KNN (clásicos), CNN+SVM y MobileNetV2+RF (híbridos)
- **Modelos deep learning adicionales**: DenseNet121, CNN desde cero, MobileNetV2 fine-tuning, EfficientNetB0
- **App Streamlit multiidioma** (Español, English, Português) con inicio de sesión
- **Modo oscuro/claro** con botón de alternancia clickeable (🌙/☀️)
- **Diagnóstico por consenso** entre modelos disponibles
- **Validación estadística**: Coeficiente de Matthews (MCC), prueba de McNemar, Cochran Q, Bootstrap estratificado
- **Reportes descargables** en PDF, Word (.docx) y Excel (.xlsx)
- **Ranking de modelos** con puntaje compuesto ponderado
- **Panel de estado del pipeline** (EDA, preprocesamiento, CV, tuning, selección)

---

## Requerimientos

### Hardware
| Componente | Mínimo | Recomendado |
|------------|--------|-------------|
| RAM | 8 GB | 16 GB |
| Almacenamiento | 5 GB | 10 GB |
| GPU | — | NVIDIA CUDA 8 GB+ |
| CPU | 4 núcleos | 8 núcleos |

### Software
- Python 3.10 – 3.11 (3.12+ no compatible con TensorFlow 2.13)
- TensorFlow 2.13
- CUDA Toolkit 11.8 + cuDNN 8.6 (solo GPU)

### Instalación
```bash
python -m venv venv
venv\Scripts\activate    # Windows
pip install -r requirements.txt
```

---

## Dataset

Estructura esperada en `dataset_original/`:
```
dataset_original/
├── Grape___Black_rot/
├── Grape___Esca_(Black_Measles)/
├── Grape___healthy/
└── Grape___Leaf_blight_(Isariopsis_Leaf_Spot)/
```

| Clase | Enfermedad |
|-------|-----------|
| `Black_rot` | Podredumbre negra (*Guignardia bidwellii*) |
| `Esca` | Esca / Sarampión negro |
| `Healthy` | Hoja sana |
| `Leaf_blight` | Tizón de la hoja (*Pseudocercospora vitis*) |

---

## Modelos Implementados

### Pipeline principal (5 modelos)

#### Clásicos (características manuales: HSV + LBP + RGB stats)
| ID | Modelo | Parámetros |
|----|--------|-----------|
| M1 | SVM | Kernel RBF, C=10, class_weight='balanced' |
| M2 | Random Forest | 200 árboles, class_weight='balanced' |
| M3 | KNN | k=5, euclidiana, weights='distance' |

#### Híbridos (extractor profundo + clasificador clásico)
| ID | Extractor | Clasificador |
|----|-----------|-------------|
| H1 | CNN (Conv2D 32→64→128 → Dense 256) | SVM RBF |
| H2 | MobileNetV2 (ImageNet, 1280 dims) | Random Forest |

### Modelos adicionales (standalone)
| Script | Arquitectura | Approach |
|--------|-------------|----------|
| `train_model_1_cnn.py` | CNN desde cero (Conv+Pool → Dense) | End-to-end |
| `train_model_2_mobilenet.py` | MobileNetV2 transfer learning | Fine-tuning |
| `train_model_3_efficientnetb0_fixed.py` | EfficientNetB0 transfer learning | Fine-tuning |
| `train_densenet121.py` | DenseNet121 transfer learning | Fine-tuning |

---

## Flujo de Trabajo

Ejecutar en orden desde la raíz del proyecto:

```bash
# PASO 1 — Preparar dataset (80% train / 20% test)
python src/prepare_dataset.py

# PASO 2 — Análisis Exploratorio (EDA)
python src/eda_validacion_datos.py

# PASO 3 — Preprocesamiento y aumento de datos
python src/preprocesamiento_aumento.py

# PASO 4 — Entrenamiento (5 modelos)
python src/train_m1_svm.py
python src/train_m2_random_forest.py
python src/train_m3_knn.py
python src/train_h1_cnn_svm.py
python src/train_h2_transfer_random_forest.py

# PASO 5 — Validación cruzada (5 folds, StratifiedKFold)
python src/cross_validation_modelos.py

# PASO 6 — Optimización de hiperparámetros (GridSearchCV)
python src/optimizacion_hiperparametros.py

# PASO 7 — Validación estadística (McNemar, Cochran Q, Bootstrap)
python src/validacion_estadistica_modelos.py

# PASO 8 — Comparación y selección del mejor modelo
python src/comparacion_general_modelos.py
python src/seleccion_mejor_modelo.py
python src/evaluacion_comparativa.py

# PASO 9 — Lanzar la aplicación web
streamlit run app.py
```

Credenciales: `admin` / `admin123` o `usuario` / `12345`

---

## App Web (Streamlit)

### Pestañas
- **🔍 Diagnóstico**: Sube una imagen y obtén diagnóstico individual o por consenso
- **📊 Análisis Estadístico**: MCC, McNemar, Bootstrap sobre tu propio dataset
- **🔬 Validación McNemar**: Validación emparejada entre modelos
- **📚 Información**: Documentación del sistema

### Reportes
- PDF con portada, diagnósticos, matriz de confusión, recomendaciones
- Word (.docx) con tabla de resultados y recomendaciones
- Excel (.xlsx) con datos estructurados

### Temas
- Alternancia instantánea entre **modo oscuro** y **modo claro** desde el botón en la barra lateral o en la pantalla de inicio de sesión.

## Arquitectura del Frontend

El frontend está modularizado en `ui/` para facilitar el mantenimiento:

| Módulo | Propósito |
|--------|-----------|
| `ui/theme.py` | CSS variables y estilos para modo oscuro/claro |
| `ui/components.py` | Componentes reutilizables (tarjetas, badges, stepper) |
| `ui/auth.py` | Pantalla de inicio de sesión con roles |
| `ui/layout.py` | Barra lateral, navegación por pestañas, encabezado |
| `ui/admin_dashboard.py` | Dashboard ejecutivo para admins |
| `ui/client_dashboard.py` | Inicio simplificado para clientes |
| `ui/diagnosis_view.py` | Flujo completo de diagnóstico (cargar → analizar → resultado) |
| `ui/history_view.py` | Historial de diagnósticos con SQLite |
| `ui/models_view.py` | Gestión y comparación de modelos |
| `ui/pipeline_view.py` | Estado del pipeline experimental |
| `ui/statistics_view.py` | Validación estadística (MCC, McNemar, Bootstrap) |
| `ui/reports_view.py` | Visualización y descarga de reportes |
| `ui/info_view.py` | Información educativa para clientes |

La persistencia se maneja mediante SQLite en `database/repository.py`, preparado para migrar a PostgreSQL.

---

## Estructura del Repositorio

```
VineGuard-AI/
├── dataset_original/       # Imágenes crudas (4 clases)
│   ├── Grape___Black_rot/
│   ├── Grape___Esca_(Black_Measles)/
│   ├── Grape___healthy/
│   └── Grape___Leaf_blight_(Isariopsis_Leaf_Spot)/
├── dataset/                # Dataset procesado (train/test 80/20)
│   ├── train/
│   └── test/
├── models/                 # Modelos entrenados
│   ├── modelo_final/       # Mejor modelo (H1) en formato listo para producción
│   ├── svm_model.pkl
│   ├── random_forest_model.pkl
│   ├── knn_model.pkl / knn_scaler.pkl
│   ├── cnn_feature_extractor.h5 / cnn_svm_model.pkl
│   ├── transfer_feature_extractor.h5 / transfer_random_forest_model.pkl
│   └── ...
├── reports/
│   ├── eda/                # Estadísticas, gráficos, validación
│   ├── preprocessing/      # Ejemplos de aumento de datos
│   ├── modelos/            # Métricas por modelo, CV, tuning, ranking
│   │   ├── m1_svm/
│   │   ├── m2_random_forest/
│   │   ├── m3_knn/
│   │   ├── h1_cnn_svm/
│   │   ├── h2_transfer_rf/
│   │   ├── cross_validation/
│   │   ├── tuning/
│   │   ├── comparativos/
│   │   ├── ranking_modelos.csv
│   │   └── mejor_modelo.txt
│   └── estadistica/        # McNemar, Cochran Q, Bootstrap
├── src/                    # Módulos y scripts
│   ├── mantenedor.py       # Constantes, rutas, configuración central
│   ├── prepare_dataset.py
│   ├── eda_validacion_datos.py
│   ├── preprocesamiento_aumento.py
│   ├── extract_features.py
│   ├── preprocesamiento_h2.py
│   ├── predecir_imagen.py  # Motor de predicción (app + CLI)
│   ├── train_m1_svm.py
│   ├── train_m2_random_forest.py
│   ├── train_m3_knn.py
│   ├── train_h1_cnn_svm.py
│   ├── train_h2_transfer_random_forest.py
│   ├── train_densenet121.py
│   ├── train_model_1_cnn.py
│   ├── train_model_2_mobilenet.py
│   ├── train_model_3_efficientnetb0_fixed.py
│   ├── cross_validation_modelos.py
│   ├── optimizacion_hiperparametros.py
│   ├── validacion_estadistica_modelos.py
│   ├── comparacion_general_modelos.py
│   ├── seleccion_mejor_modelo.py
│   ├── evaluacion_comparativa.py
│   └── evaluacion_visual.py
├── app.py                  # Punto de entrada (orquestador de módulos)
├── ui/                     # Módulos de interfaz de usuario
│   ├── __init__.py
│   ├── theme.py            # Sistema de temas (oscuro/claro)
│   ├── components.py       # Componentes reutilizables
│   ├── auth.py             # Autenticación y login
│   ├── layout.py           # Barra lateral, navegación, encabezado
│   ├── admin_dashboard.py  # Dashboard administrativo
│   ├── client_dashboard.py # Dashboard del cliente
│   ├── diagnosis_view.py   # Flujo de diagnóstico
│   ├── history_view.py     # Historial de diagnósticos
│   ├── models_view.py      # Gestión de modelos
│   ├── pipeline_view.py    # Estado del pipeline
│   ├── statistics_view.py  # Estadísticas y validación
│   ├── reports_view.py     # Reportes
│   └── info_view.py        # Información educativa
├── database/               # Capa de persistencia
│   ├── __init__.py
│   └── repository.py       # SQLite (preparado para migración a PostgreSQL)
├── data/                   # Base de datos SQLite (generada automáticamente)
├── requirements.txt
└── README.md
```

---

## Validación Estadística

| Prueba | Propósito |
|--------|----------|
| **McNemar** (exploratorio) | Comparación por pares de modelos |
| **Cochran Q** (global) | Determina si hay diferencias globales entre modelos |
| **McNemar + Holm** (post-hoc) | Comparaciones múltiples con corrección (solo si Cochran Q significativo) |
| **Bootstrap estratificado** | IC 95% para Accuracy, F1, MCC |
| **Tamaño del efecto** | Diferencia de métricas y Odds Ratio |
| **Matthews (MCC)** | Coeficiente de correlación multiclase |

---

## Referencias

1. PlantVillage Grapevine Disease Dataset — Kaggle
2. MobileNetV2: Inverted Residuals and Linear Bottlenecks — CVPR 2018
3. DenseNet: Densely Connected Convolutional Networks — CVPR 2017
4. EfficientNet: Rethinking Model Scaling — ICML 2019
5. Matthews Correlation Coefficient — Biochimica et Biophysica Acta, 1975
6. McNemar Test — Psychometrika, 1947
7. Cochran Q Test — Biometrika, 1950
