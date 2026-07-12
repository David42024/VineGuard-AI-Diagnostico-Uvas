# VineGuard AI — Sistema Inteligente para el Diagnóstico de Enfermedades Foliares en Hojas de Uva

[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](#)
[![License: MIT](https://img.shields.io/badge/License-MIT-green)](#LICENSE)
[![Streamlit](https://img.shields.io/badge/Streamlit-App-orange)](#app.py)

**VineGuard AI** es una plataforma basada en Inteligencia Artificial para la detección temprana y precisa de enfermedades foliares en cultivos de vid mediante **modelos clásicos**, **modelos híbridos** y **aprendizaje profundo**.

---

## Requerimientos del Sistema

### Hardware
| Componente | Mínimo | Recomendado |
|------------|--------|-------------|
| RAM | 8 GB | 16 GB |
| Almacenamiento | 5 GB libres | 10 GB libres |
| GPU | — | NVIDIA CUDA 8 GB+ VRAM |
| CPU | 4 núcleos | 8 núcleos |

### Software
- **Sistema operativo:** Windows 10/11, Linux (Ubuntu 20.04+), macOS 12+
- **Python:** 3.10 — 3.11 (3.12+ no compatible con TensorFlow 2.13)
- **TensorFlow:** 2.13 (CPU) / 2.13 cuDNN (GPU)
- **CUDA Toolkit:** 11.8 + cuDNN 8.6 (solo GPU)

### Instalación

```bash
# 1. Clonar o descargar el repositorio
# 2. Crear entorno virtual
python -m venv venv

# 3. Activar entorno
# Windows:
venv\Scripts\activate
# Linux/macOS:
# source venv/bin/activate

# 4. Instalar dependencias
pip install -r requirements.txt
```

> **Nota:** Si se dispone de GPU NVIDIA, instalar TensorFlow con soporte CUDA:
> ```bash
> pip install tensorflow[and-cuda]==2.13.0
> ```

---

## Estructura del Dataset

Colocar las imágenes originales en `dataset_original/` con la siguiente estructura:

```
dataset_original/
├── Grape___Black_rot/
├── Grape___Esca_(Black_Measles)/
├── Grape___healthy/
└── Grape___Leaf_blight_(Isariopsis_Leaf_Spot)/
```

## Clases del Dataset

| Clase | Nombre científico | Descripción |
|-------|-----------------|-------------|
| `Black_rot` | *Guignardia bidwellii* | Podredumbre negra |
| `Esca` | Complejo fúngico vascular | Esca (Sarampión Negro) |
| `Healthy` | — | Hoja sana |
| `Leaf_blight` | *Pseudocercospora vitis* | Tizón de la hoja |

## Modelos Implementados

### Modelos Clásicos (características manuales)
| ID | Modelo | Características |
|----|--------|-----------------|
| M1 | SVM (RBF, C=10) | Color HSV + LBP + Estadísticas RGB |
| M2 | Random Forest (200 árboles) | Color HSV + LBP + Estadísticas RGB |
| M3 | KNN (k=5, euclidiana) | Color HSV + LBP + Estadísticas RGB |

### Modelos Híbridos (extractor profundo + clasificador clásico)
| ID | Modelo | Extractor | Clasificador |
|----|--------|-----------|-------------|
| H1 | CNN + SVM | CNN Simple (256 dims) | SVM RBF |
| H2 | Transfer + RF | MobileNetV2 ImageNet (1280 dims) | Random Forest |

## Flujo de Trabajo Completo (Segun Requerimientos Docente)

Ejecutar en orden desde la raíz del proyecto:

```bash
# PASO 1 — Preparar dataset (80% train / 20% test)
python src/prepare_dataset.py

# PASO 2 — Análisis Exploratorio de Datos (EDA) y limpieza de datos
python src/eda_validacion_datos.py

# PASO 3 — Preprocesamiento y aumento de datos
python src/preprocesamiento_aumento.py

# PASO 4 — Entrenamiento de modelos (3 clásicos + 2 híbridos)
# (Genera matrices de confusión, curvas ROC, guarda modelos para usar sin reentrenar)
python src/train_m1_svm.py
python src/train_m2_random_forest.py
python src/train_m3_knn.py
python src/train_h1_cnn_svm.py
python src/train_h2_transfer_random_forest.py

# PASO 5 — Validación cruzada (configurable, default: 5 folds)
python src/cross_validation_modelos.py

# PASO 6 — Optimización de hiperparámetros (tuning con GridSearchCV)
python src/optimizacion_hiperparametros.py

# PASO 7 — Pruebas estadísticas robustas (McNemar, Cochran, Friedman, Bootstrap)
python src/validacion_estadistica_modelos.py

# PASO 8 — Selección del mejor modelo y generación de reportes
python src/seleccion_mejor_modelo.py

# PASO 9 — Lanzar la aplicación web (requiere inicio de sesión primero)
# Credenciales: admin/admin123 | usuario/12345
streamlit run app.py
```

> **Nota sobre validación cruzada**: Edita `src/cross_validation_modelos.py` para cambiar el número de folds (`n_splits`).
> **Reportes disponibles en la app**: PDF, Word (.docx) y Excel (.xlsx)
> **Tiempo estimado total** (sin GPU): 30–60 minutos. Con GPU: 10–20 minutos.

## 1. EDA y Validación de Datos

El script `eda_validacion_datos.py` analiza `dataset_original`, `dataset/train` y `dataset/test`, generando:

**Estadísticas descriptivas:**
- Cantidad total de imágenes
- Cantidad de imágenes por clase
- Media, desviación estándar, mínimo, máximo, Q1, mediana, Q3, rango, IQR
- Porcentaje por clase, distribución train/test, balance del dataset

**Análisis de dimensiones:**
- Media, desviación estándar, mínimo, máximo, cuartiles de ancho y alto
- Relación de aspecto promedio
- Modos de color detectados

**Validaciones:**
- Imágenes corruptas
- Imágenes duplicadas (hash SHA-256)
- Formatos inválidos
- Carpetas faltantes
- Clases faltantes
- Imágenes no RGB
- Imágenes demasiado pequeñas

**Reportes generados en** `reports/eda/`:
- `resumen_dataset.csv`, `estadisticas_descriptivas.csv`, `estadisticas_dimensiones.csv`
- `imagenes_invalidas.csv`, `imagenes_corruptas.csv`, `imagenes_duplicadas.csv`
- `distribucion_clases.png`, `distribucion_dimensiones.png`, `muestras_por_clase.png`

## 2. Preprocesamiento y Aumento de Datos

El módulo `preprocesamiento_aumento.py` incluye:

- Redimensionamiento a 224×224 px
- Conversión a RGB
- Normalización de píxeles [0,1]

**Aumentos aplicados solo a entrenamiento:**
- Rotación aleatoria (±30°)
- Ajuste de brillo (factor 0.6–1.4)
- Zoom (0.85–1.15)
- Contraste (0.6–1.4)
- Desplazamiento horizontal/vertical (±10%)
- Volteo horizontal
- Variaciones de escala (0.9–1.1)

**Ejemplos visuales en** `reports/preprocessing/`:
- `ejemplos_rotacion.png`, `ejemplos_brillo.png`, `ejemplos_aumento_datos.png`

## 3. Entrenamiento de Modelos

Cada script de entrenamiento guarda en `reports/modelos/`:
- `resultados_mX_nombre.csv`: accuracy, precision, recall, F1, MCC, tiempos
- `confusion_mX_nombre.csv`: matriz de confusión (CSV)
- `confusion_mX_nombre.png`: matriz de confusión (gráfico)
- `roc_mX_nombre.png`: curvas ROC multiclase One-vs-Rest

### M1 - SVM
- Kernel RBF, C=10.0, gamma='scale', probability=True, class_weight='balanced'

### M2 - Random Forest
- 200 árboles, max_depth=None, class_weight='balanced'

### M3 - KNN
- k=5, métrica euclidiana, weights='distance'

### H1 - CNN + SVM
- CNN: Conv2D(32→64→128) + GlobalAveragePooling + Dense(256)
- Split estratificado 85/15 train/val, EarlyStopping, ReduceLROnPlateau
- SVM sobre features CNN (256 dims)

### H2 - MobileNetV2 + Random Forest
- MobileNetV2 preentrenado (ImageNet) como extractor (1280 dims)
- Random Forest sobre embeddings

## 4. Cross Validation

`cross_validation_modelos.py`:
- **StratifiedKFold** con 5 folds
- Reporta por modelo: accuracy promedio, desviación estándar, F1 promedio, MCC promedio
- Genera `reports/modelos/cross_validation_resultados.csv`
- Genera gráfico `reports/modelos/cross_validation_comparacion.png`

## 5. Optimización de Hiperparámetros

`optimizacion_hiperparametros.py` con GridSearchCV + StratifiedKFold (3 folds):

| Modelo | Parámetros |
|--------|-----------|
| M1 - SVM | kernel: linear, rbf; C: 0.1,1,10,100; gamma: scale, auto |
| M2 - RF | n_estimators: 100,200,300; max_depth: None,10,20,30; min_samples_split: 2,5,10; min_samples_leaf: 1,2,4 |
| M3 - KNN | n_neighbors: 3,5,7,9; weights: uniform,distance; metric: euclidean,manhattan |
| H2 - Transfer+RF | n_estimators: 100,200,300; max_depth: None,10,20; min_samples_split: 2,5; min_samples_leaf: 1,2 |

Resultados guardados en `reports/modelos/`:
- `mejores_hiperparametros.csv`
- `resultados_gridsearch.csv`

## 6. Validación Estadística Robusta

`validacion_estadistica_modelos.py` implementa:

### 6.1 Prueba de McNemar
Comparación por pares de todos los modelos (10 comparaciones). Reporta b, c, estadístico χ², p-value e interpretación.

### 6.2 Prueba de Cochran's Q
Comparación simultánea de todos los modelos en términos de aciertos/errores. Reporta estadístico Q, p-value e interpretación.

### 6.3 Prueba de Friedman
Comparación por rankings. Reporta estadístico, p-value y ranking promedio por modelo.

### 6.4 Post-hoc: Wilcoxon con corrección Holm
Si Friedman indica diferencias significativas, prueba Wilcoxon signed-rank por pares con corrección de Holm.

### 6.5 Intervalos de Confianza por Bootstrap
IC 95% para Accuracy, F1-score macro y MCC con 1000 remuestreos.

### 6.6 Tamaño del Efecto
Diferencia absoluta de Accuracy, F1-score, MCC y Odds Ratio para McNemar.

### 6.7 Diebold-Mariano (complementario)
Se incluye solo como análisis complementario. La prueba principal es McNemar, Cochran's Q y Friedman, pues el proyecto es clasificación de imágenes, no series temporales.

Resultados guardados en `reports/estadistica/`.

## 7. Selección del Mejor Modelo

`seleccion_mejor_modelo.py` aplica un ranking compuesto ponderado:

| Métrica | Peso |
|---------|------|
| MCC | 30% |
| F1-score | 30% |
| Accuracy | 25% |
| Balanced Accuracy | 15% |

Se considera también:
- Estabilidad en cross-validation (desviación estándar)
- Penalización por tiempo de inferencia (5% si las métricas son similares)

Resultados en `reports/modelos/`:
- `ranking_modelos.csv`
- `mejor_modelo.txt`
- `comparacion_metricas_modelos.png`

## 8. Aplicación de Diagnóstico (Streamlit)

La app `app.py` requiere **inicio de sesión** primero (credenciales: `admin/admin123` o `usuario/12345`). Permite:
- Cargar los 5 modelos entrenados
- Subir una imagen de hoja de vid
- Obtener predicción de todos los modelos con tiempos de inferencia
- Ver el ranking de modelos con puntaje compuesto
- Visualizar matrices de confusión y curvas ROC de cada modelo
- Visualizar distribución de probabilidades por modelo
- Recibir recomendaciones de tratamiento según la enfermedad
- Descargar reportes en **PDF, Word (.docx) y Excel (.xlsx)**
- Validación estadística con dataset propio (MCC + McNemar)
- Interfaz multiidioma (Español, Inglés, Portugués)
- Panel lateral con estado del pipeline experimental completo

## Arquitectura del Repositorio

```text
VineGuard-AI/
├── dataset_original/           # Imágenes crudas
│   ├── Grape___Black_rot/
│   ├── Grape___Esca_(Black_Measles)/
│   ├── Grape___healthy/
│   └── Grape___Leaf_blight_(Isariopsis_Leaf_Spot)/
├── dataset/                    # Dataset procesado
│   ├── train/                  # 80%
│   └── test/                   # 20%
├── models/                     # Modelos entrenados
├── reports/
│   ├── eda/                    # Reportes EDA
│   ├── modelos/                # Métricas, CV, ranking
│   ├── estadistica/            # Validación estadística
│   └── preprocessing/          # Ejemplos de aumento
├── src/                        # Módulos y scripts
│   ├── mantenedor.py           # Configuración central
│   ├── prepare_dataset.py      # División 80/20
│   ├── eda_validacion_datos.py # EDA y validación
│   ├── preprocesamiento_aumento.py  # Aumento de datos
│   ├── extract_features.py     # Extracción de características
│   ├── train_m1_svm.py         # M1: SVM
│   ├── train_m2_random_forest.py   # M2: Random Forest
│   ├── train_m3_knn.py         # M3: KNN
│   ├── train_h1_cnn_svm.py     # H1: CNN + SVM
│   ├── train_h2_transfer_random_forest.py  # H2: MobileNetV2 + RF
│   ├── cross_validation_modelos.py     # Validación cruzada
│   ├── optimizacion_hiperparametros.py # GridSearch
│   ├── validacion_estadistica_modelos.py  # Pruebas estadísticas
│   ├── seleccion_mejor_modelo.py    # Ranking y selección
│   └── evaluacion_visual.py         # Matrices de confusión y curvas ROC
├── app.py                      # Interfaz Streamlit
├── requirements.txt            # Dependencias
└── README.md                   # Documentación
```

## 9. Evaluación Visual de Modelos

Cada script de entrenamiento genera automáticamente dos gráficos PNG en `reports/modelos/`:

### Matriz de Confusión
- Visualización de la matriz de confusión con colores según frecuencia
- Eje X: predicción, Eje Y: real
- Valores numéricos en cada celda
- Guardado como `confusion_M1_svm.png`, `confusion_M2_random_forest.png`, etc.

### Curvas ROC (One-vs-Rest)
- Curva ROC por clase con AUC (Área Bajo la Curva)
- Curva de micro-promedio global
- Línea diagonal de referencia (clasificador aleatorio)
- Guardado como `roc_M1_svm.png`, `roc_M2_random_forest.png`, etc.

### Visualización en la App
Al realizar un diagnóstico en la interfaz Streamlit, si existen los archivos PNG, se muestran automáticamente en la pestaña de diagnóstico debajo del ranking de modelos, permitiendo comparar visualmente el rendimiento de los 5 modelos.

---

## Referencias Bibliográficas

1. Mishra, P. *PlantVillage Grapevine Disease Dataset*. Kaggle.
2. Sandler, M. et al. *MobileNetV2: Inverted Residuals and Linear Bottlenecks*, CVPR 2018.
3. Hughes, D. & Salathé, M. *An open access repository of images on plant health*, 2015.
4. Matthews, B.W. *Comparison of the predicted and observed secondary structure of T4 phage lysozyme*. Biochimica et Biophysica Acta, 1975.
5. McNemar, Q. *Note on the sampling error of the difference between correlated proportions or percentages*. Psychometrika, 1947.
6. Friedman, M. *The use of ranks to avoid the assumption of normality implicit in the analysis of variance*. Journal of the American Statistical Association, 1937.
7. Cochran, W.G. *The comparison of percentages in matched samples*. Biometrika, 1950.
8. Nemenyi, P. *Distribution-free multiple comparisons*. PhD Thesis, Princeton University, 1963.
