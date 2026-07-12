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

# PASO 5 — Validación cruzada (5 folds, StratifiedKFold)
python src/cross_validation_modelos.py

# PASO 6 — Optimización de hiperparámetros (tuning con GridSearchCV)
python src/optimizacion_hiperparametros.py

# PASO 7 — Validación estadística (McNemar, Cochran Q, Bootstrap estratificado)
python src/validacion_estadistica_modelos.py

# PASO 8 — Comparación general y selección del mejor modelo
python src/comparacion_general_modelos.py
python src/seleccion_mejor_modelo.py
python src/evaluacion_comparativa.py

# PASO 9 — Lanzar la aplicación web (requiere inicio de sesión primero)
# Credenciales: admin/admin123 | usuario/12345
streamlit run app.py
```

> **Nota**: Edita `src/optimizacion_hiperparametros.py` para cambiar entre `METODO_BUSQUEDA="grid"` y `"random"`.
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

Cada script de entrenamiento guarda en su directorio individual bajo `reports/modelos/`:
| Modelo | Directorio | Archivos |
|--------|-----------|----------|
| M1 | `m1_svm/` | `resultados_m1_svm.csv`, `confusion_m1_svm.csv/png`, `roc_m1_svm.png` |
| M2 | `m2_random_forest/` | `resultados_m2_random_forest.csv`, `confusion_m2_random_forest.csv/png`, `roc_m2_random_forest.png` |
| M3 | `m3_knn/` | `resultados_m3_knn.csv`, `confusion_m3_knn.csv/png`, `roc_m3_knn.png` |
| H1 | `h1_cnn_svm/` | `resultados_h1_cnn_svm.csv`, `confusion_h1_cnn_svm.csv/png`, `roc_h1_cnn_svm.png` |
| H2 | `h2_transfer_rf/` | `resultados_h2_transfer_rf.csv`, `confusion_h2_transfer_rf.csv/png`, `roc_h2_transfer_rf.png` |

Cada CSV contiene: accuracy, precision, recall, F1-score (por clase y macro), MCC, tiempo de entrenamiento, tiempo de evaluación y tiempo total de proceso. Los tiempos se miden con `time.perf_counter()`.

### M1 - SVM
- Kernel RBF, C=10.0, gamma='scale', `probability=True`, class_weight='balanced'
- Pipeline con `StandardScaler` embebido

### M2 - Random Forest
- 200 árboles, max_depth=None, class_weight='balanced'
- No requiere escalador (basado en árboles)

### M3 - KNN
- k=5, métrica euclidiana, weights='distance'
- Pipeline con `StandardScaler` embebido

### H1 - CNN + SVM
- CNN: Conv2D(32→64→128) + GlobalAveragePooling + Dense(256)
- Split estratificado 85/15 train/val, EarlyStopping, ReduceLROnPlateau
- SVM sobre features CNN (256 dims)

### H2 - MobileNetV2 + Random Forest
- MobileNetV2 preentrenado (ImageNet) como extractor (1280 dims)
- Random Forest sobre embeddings

## 4. Cross Validation

`cross_validation_modelos.py`:
- **StratifiedKFold** con 5 folds sobre entrenamiento real (sin aumento)
- Modelos evaluados: M1 (SVM), M2 (Random Forest), M3 (KNN)
- Reporta por modelo: accuracy, F1, MCC, tiempo promedio por fold
- Salida en `reports/modelos/cross_validation/`:
  - `cross_validation_resultados.csv` — resumen por modelo
  - `cross_validation_por_fold.csv` — resultados detallados por fold
  - `cross_validation_comparacion.png` — gráfico comparativo

## 5. Optimización de Hiperparámetros

`optimizacion_hiperparametros.py` con `GridSearchCV` + StratifiedKFold (3 folds).

| Modelo | Parámetros |
|--------|-----------|
| M1 - SVM | kernel: linear, rbf; C: 0.1,1,10,100; gamma: scale, auto; **probability=True** |
| M2 - RF | n_estimators: 100,200,300; max_depth: None,10,20,30; min_samples_split: 2,5,10; min_samples_leaf: 1,2,4 |
| M3 - KNN | n_neighbors: 3,5,7,9; weights: uniform,distance; metric: euclidean,manhattan |
| H2 - Transfer+RF | n_estimators: 100,200,300; max_depth: None,10,20; min_samples_split: 2,5; min_samples_leaf: 1,2 |

Resultados guardados en `reports/modelos/tuning/`:
- `mejores_hiperparametros.csv` — resumen de todos los modelos
- `gridsearch_M1_SVM_resultados.csv` — resultados detallados por modelo
- Archivos `.pkl` del mejor pipeline encontrado

## 6. Validación Estadística Robusta

`validacion_estadistica_modelos.py` implementa **5 pruebas principales + 1 complementaria** sobre las predicciones de los 5 modelos, generadas sobre la **misma secuencia ordenada de imágenes TEST** para garantizar comparación emparejada.

### 6.1 Prueba de McNemar (exploratoria por pares)
Comparación por pares de todos los modelos. Reporta discordantes `b` y `c`, estadístico, p-valor completo, método usado (exacto si `b+c ≤ 25`, chi-cuadrado con corrección en caso contrario) e interpretación.

### 6.2 Prueba de Cochran's Q (global)
Comparación simultánea de todos los modelos en términos de aciertos/errores binarios. Es la **puerta de entrada** para el post-hoc: si `p ≥ 0.05` no hay diferencias globales y se omite el post-hoc.

### 6.3 Post-hoc: McNemar con corrección Holm (condicional)
Se ejecuta **solo si Cochran Q es significativo** (`p < 0.05`). Aplica McNemar a cada par y ajusta p-valores con el procedimiento de Holm. La decisión de rechazo se calcula con p-valores completos (no redondeados); el redondeo solo afecta la salida CSV.

### 6.4 Intervalos de Confianza por Bootstrap Estratificado
IC 95% para Accuracy, F1-score macro y MCC con 1000 remuestreos, **estratificados por clase** (preserva distribución de clases en cada remuestreo).

### 6.5 Tamaño del Efecto
Para cada par de modelos: diferencia de Accuracy, F1-macro y MCC (con signo, indicando qué modelo supera al otro) y Odds Ratio de McNemar con corrección de continuidad.

### 6.6 Diebold-Mariano (complementario)
Se incluye solo como análisis complementario (diseñado originalmente para series temporales). No es la prueba principal del proyecto.

### Flujo de ejecución
```
Predicciones alineadas sobre TEST (misma secuencia)
        ↓
McNemar exploratorio por pares
        ↓
Cochran Q global
        ↓
McNemar + Holm solo si Cochran Q significativo
        ↓
Bootstrap estratificado al 95%
        ↓
Diferencias de Accuracy, F1 y MCC
        ↓
Diebold-Mariano complementario
```

Resultados guardados en `reports/estadistica/`:
- `mcnemar_resultados.csv`
- `cochran_q_resultado.csv`
- `mcnemar_holm_posthoc.csv` (solo si Cochran Q significativo)
- `intervalos_confianza_bootstrap.csv`
- `tamano_efecto.csv`
- `diebold_mariano_complementario.csv`

## 7. Selección del Mejor Modelo

### 7.1 Comparación general
`comparacion_general_modelos.py` consolida las métricas de los 5 modelos desde sus directorios individuales (`reports/modelos/m1_svm/`, ..., `reports/modelos/h2_transfer_rf/`) y genera tablas de comparación en `reports/modelos/comparativos/`.

### 7.2 Ranking compuesto
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

### 7.3 Evaluación comparativa
`evaluacion_comparativa.py` genera:
- Curvas ROC comparativas de los 5 modelos
- Benchmark de tiempos de inferencia
- Análisis de throughput (imágenes/segundo)

Resultados en `reports/modelos/`:
- `ranking_modelos.csv`
- `mejor_modelo.txt`
- `comparacion_metricas_modelos.png`
- Y en `reports/modelos/comparativos/` las tablas agregadas y gráficos ROC

## 8. Módulo de Predicción Compartido

`src/predecir_imagen.py` es el motor de predicción usado tanto por CLI como por la app Streamlit:

- `predecir(ruta, modelo)` — predice una imagen con un modelo específico
- `predecir_todos(ruta)` — predice con todos los modelos disponibles
- `cargar_modelo(modelo)` — carga un modelo bajo demanda (lazy loading)
- `validar_imagen(ruta)` — valida formato, tamaño y que el archivo no esté corrupto
- `ordenar_probabilidades(dict_probs, classes_)` — ordena y valida probabilidades estrictamente

Los modelos se cargan de forma independiente (TF solo se importa dentro de H1/H2). La extracción de características clásicas se hace una sola vez para M1/M2/M3; si falla, los tres se marcan como no disponibles.

## 9. Aplicación de Diagnóstico (Streamlit)

La app `app.py` requiere **inicio de sesión** primero (credenciales: `admin/admin123` o `usuario/12345`). Permite:

- Cargar los 5 modelos entrenados de forma independiente (cada modelo tiene su propio estado de carga)
- Subir una o más imágenes de hoja de vid con validación previa (formato, tamaño)
- Obtener predicción de todos los modelos disponibles con tiempos de inferencia
- Diagnóstico por consenso: clasifica según clase más votada entre modelos disponibles (0, 1, 2, 3, 4 o 5 modelos)
- Ver el ranking de modelos con puntaje compuesto
- Visualizar matrices de confusión y curvas ROC de cada modelo
- Visualizar distribución de probabilidades por modelo (con manejo seguro de `confidence=None`)
- Recibir recomendaciones de tratamiento según la enfermedad
- Descargar reportes en **PDF, Word (.docx) y Excel (.xlsx)** con información completa (modelo, clases, probabilidades, metadata)
- Validación estadística: McNemar exacto (via `statsmodels`), Cochran Q, bootstrap estratificado
- Interfaz multiidioma (Español, Inglés, Portugués)
- Panel lateral con estado del pipeline experimental (✅/⬜), incluyendo validación de contenido real de cada artefacto

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
│   ├── preprocessing/          # Ejemplos de aumento
│   ├── modelos/
│   │   ├── m1_svm/             # Métricas M1
│   │   ├── m2_random_forest/   # Métricas M2
│   │   ├── m3_knn/             # Métricas M3
│   │   ├── h1_cnn_svm/         # Métricas H1
│   │   ├── h2_transfer_rf/     # Métricas H2
│   │   ├── tuning/             # Hiperparámetros optimizados
│   │   ├── cross_validation/   # Resultados CV
│   │   └── comparativos/       # Tablas agregadas y ranking
│   └── estadistica/            # Validación estadística
├── src/                        # Módulos y scripts
│   ├── mantenedor.py           # Configuración central (constantes, rutas)
│   ├── prepare_dataset.py      # División 80/20
│   ├── eda_validacion_datos.py # EDA y validación
│   ├── preprocesamiento_aumento.py  # Aumento de datos
│   ├── extract_features.py     # Extracción de características
│   ├── preprocesamiento_h2.py  # Extracción de embeddings MobileNetV2
│   ├── predecir_imagen.py      # Motor de predicción compartido
│   ├── train_m1_svm.py         # M1: SVM
│   ├── train_m2_random_forest.py   # M2: Random Forest
│   ├── train_m3_knn.py         # M3: KNN
│   ├── train_h1_cnn_svm.py     # H1: CNN + SVM
│   ├── train_h2_transfer_random_forest.py  # H2: MobileNetV2 + RF
│   ├── cross_validation_modelos.py     # Validación cruzada
│   ├── optimizacion_hiperparametros.py # GridSearch / RandomSearch
│   ├── validacion_estadistica_modelos.py  # McNemar, Cochran Q, bootstrap
│   ├── comparacion_general_modelos.py    # Tabla comparativa
│   ├── seleccion_mejor_modelo.py    # Ranking y selección
│   ├── evaluacion_comparativa.py    # ROC comparativa y benchmark
│   └── evaluacion_visual.py         # Matrices de confusión y curvas ROC
├── app.py                      # Interfaz Streamlit (diagnóstico, reportes, estadísticas)
├── requirements.txt            # Dependencias
└── README.md                   # Documentación
```

## 10. Evaluación Visual de Modelos

Cada script de entrenamiento genera automáticamente dos gráficos PNG en su directorio individual (`reports/modelos/mX_*/`):

### Matriz de Confusión
- Visualización con colores según frecuencia
- Eje X: predicción, Eje Y: real
- Valores numéricos en cada celda

### Curvas ROC (One-vs-Rest)
- Curva ROC por clase con AUC
- Curva de micro-promedio global
- Línea diagonal de referencia

### Visualización en la App
Al realizar un diagnóstico, si existen los archivos PNG, se muestran automáticamente en la pestaña de diagnóstico debajo del ranking de modelos. Además, `evaluacion_comparativa.py` genera una superposición ROC de los 5 modelos en `reports/modelos/comparativos/comparacion_roc_modelos.png`.

---

## 11. Referencias Bibliográficas

1. Mishra, P. *PlantVillage Grapevine Disease Dataset*. Kaggle.
2. Sandler, M. et al. *MobileNetV2: Inverted Residuals and Linear Bottlenecks*, CVPR 2018.
3. Hughes, D. & Salathé, M. *An open access repository of images on plant health*, 2015.
4. Matthews, B.W. *Comparison of the predicted and observed secondary structure of T4 phage lysozyme*. Biochimica et Biophysica Acta, 1975.
5. McNemar, Q. *Note on the sampling error of the difference between correlated proportions or percentages*. Psychometrika, 1947.
6. Friedman, M. *The use of ranks to avoid the assumption of normality implicit in the analysis of variance*. Journal of the American Statistical Association, 1937.
7. Cochran, W.G. *The comparison of percentages in matched samples*. Biometrika, 1950.
8. Nemenyi, P. *Distribution-free multiple comparisons*. PhD Thesis, Princeton University, 1963.
