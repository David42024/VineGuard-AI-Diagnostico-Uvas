# VineGuard AI — Diagnóstico Inteligente de Enfermedades en Hojas de Vid

[![Python](https://img.shields.io/badge/Python-3.11-blue)](#)
[![Streamlit](https://img.shields.io/badge/Streamlit-AI%20Lab-ff4b4b)](#)
[![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688)](#)
[![Next.js](https://img.shields.io/badge/Next.js-Frontend-black)](#)
[![React](https://img.shields.io/badge/React-18-61dafb)](#)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-3.4-38bdf8)](#)
[![License: MIT](https://img.shields.io/badge/License-MIT-green)](#)

**VineGuard AI** es una plataforma de inteligencia artificial para la detección temprana de enfermedades foliares en vid. Integra modelos clásicos, modelos híbridos y redes neuronales, junto con validación cruzada, optimización de hiperparámetros, pruebas estadísticas robustas y generación de reportes.

El sistema utiliza una arquitectura separada por responsabilidades:

- **Streamlit AI Lab:** ejecución y visualización del pipeline de Machine Learning.
- **FastAPI:** autenticación, diagnósticos, acceso a modelos, estadísticas y reportes.
- **Next.js:** aplicación web final para administradores y clientes.

---

## Características principales

- Cinco modelos integrados:
  - M1 — SVM
  - M2 — Random Forest
  - M3 — KNN
  - H1 — CNN + SVM
  - H2 — MobileNetV2 + Random Forest
- Diagnóstico individual y por consenso.
- Lectura y validación del dataset.
- Análisis exploratorio de datos.
- Preprocesamiento y aumento de imágenes.
- Validación cruzada configurable.
- Optimización de hiperparámetros.
- Pruebas estadísticas robustas.
- Selección automática del mejor modelo.
- Persistencia de modelos en `.h5` y `.pkl`.
- Historial de diagnósticos en SQLite.
- Reportes en CSV, PNG, DOCX, PDF y XLSX.
- Autenticación con roles administrador y cliente.
- Interfaz bilingüe español/inglés.
- Modo claro y oscuro.
- Chatbot de ayuda por texto y voz.
- Frontend moderno con Next.js, React y Tailwind CSS.

---

## Arquitectura

```text
                          ┌──────────────────────────┐
                          │     Streamlit AI Lab     │
                          │ EDA, entrenamiento, CV,  │
                          │ tuning y estadística     │
                          └────────────┬─────────────┘
                                       │
                                       ▼
                             ┌──────────────────────┐
                             │ models/ + reports/  │
                             │ .h5, .pkl, CSV, PNG │
                             └──────────┬───────────┘
                                        │
                                        ▼
                             ┌──────────────────────┐
                             │       FastAPI        │
                             │ Auth, diagnóstico,   │
                             │ modelos y reportes   │
                             └──────────┬───────────┘
                                        │ HTTP / JSON
                                        ▼
                             ┌──────────────────────┐
                             │ Next.js + React      │
                             │ Aplicación final     │
                             └──────────────────────┘

                             ┌──────────────────────┐
                             │ SQLite              │
                             │ users, diagnostics, │
                             │ audit_log           │
                             └──────────────────────┘
```

La descripción completa se encuentra en [`ARCHITECTURE.md`](./ARCHITECTURE.md).

---

## Persistencia

VineGuard AI utiliza dos mecanismos de persistencia separados.

### SQLite

Archivo:

```text
data/vinguard.db
```

Tablas principales:

| Tabla | Contenido |
|---|---|
| `users` | Cuentas, roles, contraseñas y último acceso |
| `diagnostics` | Resultado, confianza, modelo usado y fecha |
| `audit_log` | Accesos y acciones |
| `models` | Metadatos básicos opcionales |

### Artefactos de Machine Learning

| Ruta | Contenido |
|---|---|
| `models/*.pkl` | Clasificadores clásicos e híbridos |
| `models/*.h5` | Extractores CNN y modelos Keras |
| `reports/modelos/` | Métricas, ranking, CV y tuning |
| `reports/estadistica/` | McNemar, Cochran-Q, Bootstrap y tamaños de efecto |
| `reports/eda/` | Resultados del análisis exploratorio |
| `reports/preprocessing/` | Ejemplos de aumento de datos |

> SQLite no almacena los pesos entrenados ni los resultados completos del pipeline.

---

## Dataset

Estructura esperada:

```text
dataset_original/
├── Grape___Black_rot/
├── Grape___Esca_(Black_Measles)/
├── Grape___healthy/
└── Grape___Leaf_blight_(Isariopsis_Leaf_Spot)/
```

Clases utilizadas:

| Clase | Descripción |
|---|---|
| `Black_rot` | Podredumbre negra |
| `Esca` | Esca o sarampión negro |
| `Healthy` | Hoja sana |
| `Leaf_blight` | Tizón de la hoja |

La preparación genera una división estratificada:

```text
dataset/
├── train/
└── test/
```

---

## Modelos implementados

| ID | Modelo | Tipo | Artefactos |
|---|---|---|---|
| `M1` | SVM | Clásico | `svm_model.pkl`, `svm_scaler.pkl` |
| `M2` | Random Forest | Clásico | `random_forest_model.pkl` |
| `M3` | KNN | Clásico | `knn_model.pkl`, `knn_scaler.pkl` |
| `H1` | CNN + SVM | Híbrido | `cnn_feature_extractor.h5`, `h1_svm_classifier.pkl` |
| `H2` | MobileNetV2 + RF | Híbrido | `transfer_feature_extractor.h5`, `transfer_random_forest_model.pkl` |

El modelo H1 está compuesto por dos archivos:

```text
Extractor CNN (.h5) + Clasificador SVM (.pkl)
```

---

## Pipeline de Machine Learning

Ejecutar desde la raíz del proyecto:

```bash
# 1. Preparar dataset
python src/prepare_dataset.py

# 2. Análisis exploratorio
python src/eda_validacion_datos.py

# 3. Preprocesamiento y aumento
python src/preprocesamiento_aumento.py

# 4. Entrenamiento
python src/train_m1_svm.py
python src/train_m2_random_forest.py
python src/train_m3_knn.py
python src/train_h1_cnn_svm.py
python src/train_h2_transfer_random_forest.py

# 5. Validación cruzada
python src/cross_validation_modelos.py

# 6. Optimización de hiperparámetros
python src/optimizacion_hiperparametros.py

# 7. Validación estadística
python src/validacion_estadistica_modelos.py

# 8. Comparación y selección
python src/comparacion_general_modelos.py
python src/seleccion_mejor_modelo.py
python src/evaluacion_comparativa.py
```

---

## Pruebas estadísticas

| Prueba | Propósito |
|---|---|
| MCC | Medir desempeño multiclase |
| Cochran Q | Comparar globalmente los modelos |
| McNemar | Comparación por pares |
| McNemar + Holm | Comparaciones múltiples corregidas |
| Bootstrap estratificado | Intervalos de confianza |
| Tamaño del efecto | Magnitud de diferencias |
| Odds Ratio | Comparación relativa de errores |

---

## Requisitos

### Software

- Python 3.11
- Node.js 20 o superior
- npm 10 o superior
- TensorFlow 2.13
- scikit-learn 1.3
- SQLite
- Git

### Hardware recomendado

| Componente | Mínimo | Recomendado |
|---|---:|---:|
| RAM | 8 GB | 16 GB |
| Almacenamiento | 5 GB | 10 GB |
| CPU | 4 núcleos | 8 núcleos |
| GPU | No obligatoria | NVIDIA con CUDA |

---

## Instalación

## 1. Clonar el repositorio

```bash
git clone https://github.com/David42024/VineGuard-AI-Diagnostico-Uvas.git
cd VineGuard-AI-Diagnostico-Uvas
```

## 2. Configurar Python

### Windows

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### Linux o macOS

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 3. Configurar variables de entorno

Crear un archivo `.env` en la raíz:

```env
SECRET_KEY=change-this-secret-key
DATABASE_URL=sqlite:///./data/vinguard.db
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

Para el frontend, crear `frontend/.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

---

## Ejecución local

## Streamlit AI Lab

```bash
streamlit run app.py
```

Disponible normalmente en:

```text
http://localhost:8501
```

## FastAPI

```bash
uvicorn backend.main:app --reload
```

Disponible normalmente en:

```text
http://localhost:8000
```

Documentación Swagger:

```text
http://localhost:8000/docs
```

## Next.js

```bash
cd frontend
npm install
npm run dev
```

Disponible normalmente en:

```text
http://localhost:3000
```

---

## Credenciales de demostración

| Usuario | Contraseña | Rol |
|---|---|---|
| `admin` | `admin123` | Administrador |
| `usuario` | `12345` | Cliente |

> Cambiar estas credenciales antes de cualquier despliegue público.

---

## Flujo de diagnóstico

```text
Usuario sube una imagen
        ↓
Next.js envía FormData a FastAPI
        ↓
FastAPI valida JWT
        ↓
FastAPI carga el modelo seleccionado
        ↓
Se realiza la inferencia
        ↓
El resultado se guarda en SQLite
        ↓
FastAPI devuelve JSON
        ↓
Next.js muestra el diagnóstico
```

Ejemplo de respuesta:

```json
{
  "id": 35,
  "result": "Black_rot",
  "confidence": 0.9421,
  "model_used": "H1",
  "probabilities": {
    "Black_rot": 0.9421,
    "Esca": 0.0312,
    "Healthy": 0.0104,
    "Leaf_blight": 0.0163
  }
}
```

---

## Endpoints principales

| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/api/v1/auth/login` | Iniciar sesión |
| `GET` | `/api/v1/auth/me` | Obtener usuario actual |
| `POST` | `/api/v1/diagnoses` | Crear diagnóstico |
| `GET` | `/api/v1/diagnoses` | Listar diagnósticos |
| `GET` | `/api/v1/models` | Listar modelos |
| `GET` | `/api/v1/models/ranking` | Obtener ranking |
| `GET` | `/api/v1/models/best` | Obtener mejor modelo |
| `GET` | `/api/v1/pipeline/status` | Estado del pipeline |
| `GET` | `/api/v1/statistics/summary` | Resumen estadístico |
| `GET` | `/api/v1/reports` | Listar reportes |
| `GET` | `/api/v1/users` | Listar usuarios |

---

## Estructura del repositorio

```text
VineGuard-AI/
├── app.py
├── ARCHITECTURE.md
├── backend/
│   ├── main.py
│   ├── api/
│   ├── core/
│   ├── database/
│   └── schemas/
├── frontend/
│   └── src/
│       ├── app/
│       ├── components/
│       ├── lib/
│       ├── store/
│       └── i18n/
├── database/
│   └── repository.py
├── scripts/
├── src/
│   ├── services/
│   ├── mantenedor.py
│   ├── predecir_imagen.py
│   ├── prepare_dataset.py
│   ├── eda_validacion_datos.py
│   ├── preprocesamiento_aumento.py
│   ├── train_m1_svm.py
│   ├── train_m2_random_forest.py
│   ├── train_m3_knn.py
│   ├── train_h1_cnn_svm.py
│   ├── train_h2_transfer_random_forest.py
│   ├── cross_validation_modelos.py
│   ├── optimizacion_hiperparametros.py
│   ├── validacion_estadistica_modelos.py
│   └── seleccion_mejor_modelo.py
├── ui/
├── data/
│   └── vinguard.db
├── models/
├── reports/
├── dataset/
├── dataset_original/
├── requirements.txt
└── README.md
```

---

## Despliegue

| Componente | Plataforma recomendada |
|---|---|
| Streamlit AI Lab | Render |
| FastAPI | Render |
| Next.js | Vercel |
| Código fuente | GitHub |
| Documentación y seguimiento | Jira |

### Streamlit en Render

```bash
streamlit run app.py --server.port $PORT --server.address 0.0.0.0
```

### FastAPI en Render

```bash
uvicorn backend.main:app --host 0.0.0.0 --port $PORT
```

### Next.js en Vercel

```env
NEXT_PUBLIC_API_URL=https://vinguard-api.onrender.com/api/v1
```

> SQLite debe usar almacenamiento persistente en Render para evitar la pérdida de usuarios y diagnósticos.

---

## Backups

Respaldar:

```text
data/vinguard.db
models/
reports/
```

- `data/vinguard.db`: usuarios, diagnósticos y auditoría.
- `models/`: artefactos entrenados.
- `reports/`: métricas, gráficos y resultados.

---

## Licencia

Este proyecto se distribuye bajo la licencia MIT.

---

## Autores

Proyecto académico desarrollado para la implementación de un sistema inteligente de diagnóstico de enfermedades en hojas de vid.