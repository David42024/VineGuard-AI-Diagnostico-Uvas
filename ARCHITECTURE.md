# VineGuard AI — Arquitectura del Sistema

> Sistema de diagnóstico inteligente de enfermedades en hojas de vid usando redes neuronales convolucionales y modelos clásicos de ML.

---

## 1. Vista General

```
┌─────────────────────────────────────────────────────────────┐
│                    USUARIO (Browser/Terminal)                │
└──────────┬────────────────────────────────┬─────────────────┘
           │                                │
     ┌─────▼──────┐                  ┌──────▼──────┐
     │  Streamlit  │                  │   Next.js   │
     │  (app.py)   │                  │  Frontend   │
     └─────┬──────┘                  └──────┬──────┘
           │                                │
           │                           HTTP │ (JSON)
           │                                │
           │                    ┌───────────▼───────────┐
           │                    │   FastAPI Backend      │
           │                    │   localhost:8000       │
           │                    └───────────┬───────────┘
           │                                │
           ├──────────────┬─────────────────┤
           │              │                 │
     ┌─────▼────┐  ┌─────▼──────┐   ┌──────▼──────┐
     │  SQLite  │  │   ML       │   │  Reports/   │
     │  DB      │  │   Models   │   │  CSVs       │
     │ vinguard │  │   (Python) │   │  (FS)       │
     └──────────┘  └────────────┘   └─────────────┘
```

---

## 2. Componentes

### 2.1 Streamlit App (`app.py` + `ui/`)

| Archivo | Responsabilidad |
|---------|----------------|
| `app.py` | Entry point, session state, page routing, login gate |
| `ui/auth.py` | Login/register screen, auth validation |
| `ui/layout.py` | Sidebar navigation, header, theme toggle |
| `ui/theme.py` | CSS variables, light/dark mode |
| `ui/admin_dashboard.py` | Admin executive summary, metrics, charts |
| `ui/client_dashboard.py` | Client home, recent diagnostics |
| `ui/diagnosis_view.py` | Image upload + prediction flow |
| `ui/history_view.py` | Diagnostic history table/filter |
| `ui/models_view.py` | Model status, metrics, test form |
| `ui/pipeline_view.py` | Pipeline stage progress visualization |
| `ui/statistics_view.py` | Detailed stats: CV, bootstrap, McNemar, etc. |
| `ui/reports_view.py` | Generated report listing + download |
| `ui/info_view.py` | Disease info cards, about system |
| `ui/components.py` | Reusable UI widgets (metric cards, badges, etc.) |

### 2.2 FastAPI Backend (`backend/`)

| Archivo | Responsabilidad |
|---------|----------------|
| `backend/main.py` | FastAPI app creation, CORS, lifespan, error handlers |
| `backend/core/config.py` | `Settings` class via pydantic-settings (DB_URL, SECRET_KEY, etc.) |
| `backend/core/security.py` | JWT creation/verification, bcrypt password hashing, `get_current_user` dependency |
| `backend/database/database.py` | SQLAlchemy engine, ORM models (UserModel, DiagnosticModel, AuditLogModel), `get_db` |
| `backend/api/auth.py` | `POST /login`, `POST /logout`, `POST /refresh`, `GET /me` |
| `backend/api/diagnosis.py` | `POST /diagnoses`, `GET /diagnoses`, `GET /diagnoses/{id}`, `DELETE /{id}`, `POST /{id}/repeat` |
| `backend/api/models.py` | `GET /models`, `GET /models/{id}`, `POST /models/test`, `GET /models/ranking`, `GET /models/best` |
| `backend/api/pipeline.py` | `GET /pipeline/status`, `GET /pipeline/stages` |
| `backend/api/statistics.py` | `GET /statistics/summary`, `/model-comparison`, `/cross-validation`, `/bootstrap`, `/mcnemar`, `/cochran` |
| `backend/api/reports.py` | `GET /reports`, `POST /reports/diagnosis/{id}`, `GET /reports/{id}/download` |
| `backend/api/users.py` | `GET /users`, `GET /users/{id}`, `PATCH /users/{id}`, `DELETE /users/{id}` |
| `backend/schemas/` | Pydantic models para request/response de cada módulo |

### 2.3 Next.js Frontend (`frontend/`)

| Archivo | Responsabilidad |
|---------|----------------|
| `src/middleware.ts` | Route protection: redirects unauthenticated users, enforces admin paths |
| `src/app/layout.tsx` | Root layout with ThemeProvider + Toaster |
| `src/app/(admin)/layout.tsx` | Admin layout: auth check, AppShell (Sidebar + Header) |
| `src/app/(admin)/admin/page.tsx` | Admin Dashboard: stats grid, charts, recent diagnostics, users |
| `src/app/(admin)/admin/statistics/page.tsx` | Detailed statistics: model comparison, CV, bootstrap, etc. |
| `src/app/(admin)/admin/models/page.tsx` | Model management: cards, metrics, test form |
| `src/app/(admin)/admin/pipeline/page.tsx` | Pipeline stage progress |
| `src/app/(admin)/admin/reports/page.tsx` | Report listing + download |
| `src/app/(admin)/admin/users/page.tsx` | User CRUD table |
| `src/app/(admin)/admin/diagnostics/page.tsx` | All diagnostics table (admin) |
| `src/app/(client)/dashboard/page.tsx` | Client home |
| `src/app/(client)/dashboard/diagnosis/page.tsx` | Upload + diagnose |
| `src/app/(client)/dashboard/history/page.tsx` | User's diagnostic history |
| `src/app/(client)/dashboard/diseases/page.tsx` | Disease info cards |
| `src/components/layout/sidebar.tsx` | Navigation sidebar with sections (Admin/Client) |
| `src/components/layout/header.tsx` | Top header with page title, user menu |
| `src/components/layout/app-shell.tsx` | Sidebar + Header + content wrapper |
| `src/components/dashboard/stats-grid.tsx` | Metric cards row |
| `src/components/dashboard/metric-card.tsx` | Single metric card |
| `src/components/charts/donut-chart.tsx` | Recharts donut |
| `src/components/charts/bar-chart.tsx` | Recharts bar |
| `src/components/charts/line-chart.tsx` | Recharts line |
| `src/lib/api.ts` | Axios instance with JWT interceptor |
| `src/lib/auth.ts` | Token/session helpers (cookies) |
| `src/store/auth-store.ts` | Zustand store: user, role, login/logout |
| `src/store/theme-store.ts` | Zustand store: sidebar, language, theme |
| `src/i18n/` | Translation files (es.json, en.json, pt.json) |

### 2.4 ML Layer (`src/`)

| Archivo | Responsabilidad |
|---------|----------------|
| `src/mantenedor.py` | Central constants: paths, class names, image sizes, seeds |
| `src/predecir_imagen.py` | Core prediction engine: 5 model implementations |
| `src/services/prediction_service.py` | Shared service: `predict_from_image()`, `predict_consensus()`, model loading with caching |
| `src/train_*.py` | Training scripts for each model variant |
| `src/evaluacion_comparativa.py` | Comparative evaluation across models |
| `src/cross_validation_modelos.py` | K-fold cross-validation |
| `src/validacion_estadistica_modelos.py` | Statistical tests: McNemar, Cochran, bootstrap |
| `src/optimizacion_hiperparametros.py` | Hyperparameter tuning (GridSearch) |
| `src/seleccion_mejor_modelo.py` | Best model selection logic |

### 2.5 Database Layer

Hay dos capas de BD que apuntan al mismo archivo SQLite:

| Archivo | Tecnología | Uso |
|---------|-----------|-----|
| `database/repository.py` | `sqlite3` (raw) | Streamlit app + algunas rutas FastAPI |
| `backend/database/database.py` | SQLAlchemy ORM | FastAPI endpoints via `get_db()` |
| `scripts/db.mjs` | `better-sqlite3` (Node.js) | Scripts de init/reset/seed |

**Tablas:**
- `users` — id, name, username, password_hash, role (admin/client), active, created_at, last_login
- `diagnostics` — id, user_id (FK), timestamp, filename, image_path, result, confidence, model_used, probabilities (JSON), inference_time_ms, analysis_type, status
- `audit_log` — id, user_id (FK), action, detail, timestamp
- `models` — id, name, type, accuracy, precision, recall, f1_score, status (creada por scripts de seed)

**Seed users:**
| Username | Password | Rol |
|----------|----------|-----|
| `admin` | `admin123` | admin |
| `usuario` | `12345` | client |

---

## 3. Flujo de Datos

### 3.1 Diagnóstico (Frontend → API → ML → DB)

```
Usuario sube imagen
        │
        ▼
Next.js /dashboard/diagnosis
  POST /api/v1/diagnoses (multipart: file + model_key)
        │
        ▼
FastAPI create_diagnosis()
  ├── Valida JWT (get_current_user)
  ├── Guarda imagen en data/uploads/
  ├── Carga modelo (load_single_model o load_all_models)
  ├── predict_from_image() o predict_consensus()
  │     └── src/predecir_imagen.py
  │           ├── Extrae características (HSV, LBP, CNN, Transfer)
  │           └── Clasifica (SVM, RF, KNN)
  ├── save_diagnostic() → SQLite (diagnostics table)
  ├── audit_log() → SQLite (audit_log table)
  └── Retorna DiagnosisResponse (JSON)
        │
        ▼
Next.js renderiza resultado
  └── Badge (Healthy/Enfermedad)
  └── Barra de confianza
  └── Tabla de probabilidades por clase
  └── Información de la enfermedad
```

### 3.2 Autenticación

```
Login form
  POST /api/v1/auth/login { username, password }
        │
        ▼
  authenticate() → SQLite (users table, SHA-256 hash)
        │
        ▼
  create_access_token() → JWT (HS256, 60min exp)
        │
        ▼
  Response: { access_token, user: { id, name, username, role } }
        │
        ▼
  Next.js: guarda token en cookie, user en Zustand store
```

### 3.3 Carga de Modelos ML

Los modelos se cargan **lazy** (on-demand) con caché:

```
1. GET /api/v1/models → get_model_status()
   └── Verifica si archivos .pkl/.h5 existen en models/

2. POST /api/v1/diagnoses (model_key="M1")
   └── load_single_model("M1")
       └── Carga SVM desde models/svm_model.pkl + scaler
       └── Almacena en dict global _modelos (caché)

3. model_key="consensus"
   └── load_all_models() → carga los 5 (si no están en caché)
   └── predict_consensus() → ejecuta los 5, vota
```

**Los 5 modelos:**

| Key | Nombre | Tipo | Archivos |
|-----|--------|------|----------|
| M1 | SVM | Classic ML | `svm_model.pkl`, `svm_scaler.pkl` |
| M2 | Random Forest | Classic ML | `random_forest_model.pkl` |
| M3 | KNN | Classic ML | `knn_model.pkl`, `knn_scaler.pkl` |
| H1 | CNN + SVM | Hybrid (H1) | `cnn_feature_extractor.h5`, `h1_svm_classifier.pkl` |
| H2 | Transfer + RF | Hybrid (H2) | `transfer_feature_extractor.h5`, `transfer_random_forest_model.pkl` |

---

## 4. API Endpoints (FastAPI)

### Auth (`/api/v1/auth`)
| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| POST | `/login` | No | Login, devuelve JWT + user |
| POST | `/logout` | JWT | Cerrar sesión |
| POST | `/refresh` | JWT | Refrescar token |
| GET | `/me` | JWT | Info del usuario actual |

### Diagnoses (`/api/v1/diagnoses`)
| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| POST | `/` | JWT | Crear diagnóstico (upload + model_key o "consensus") |
| GET | `/` | JWT | Listar diagnósticos (admin: todos, client: propios) |
| GET | `/{id}` | JWT | Detalle de diagnóstico |
| DELETE | `/{id}` | JWT | Eliminar diagnóstico |
| POST | `/{id}/repeat` | JWT | Repetir diagnóstico con misma imagen |

### Models (`/api/v1/models`)
| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| GET | `/` | JWT | Listar 5 modelos con métricas |
| GET | `/{id}` | JWT | Detalle de un modelo |
| POST | `/test` | JWT | Probar modelo con imagen |
| GET | `/ranking` | JWT | Ranking desde CSV |
| GET | `/best` | JWT | Mejor modelo desde archivo |

### Statistics (`/api/v1/statistics`)
| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| GET | `/summary` | Admin | Stats generales + distribución + ranking |
| GET | `/model-comparison` | JWT | Ranking, effect size, Diebold-Mariano |
| GET | `/cross-validation` | JWT | Resultados CV por fold |
| GET | `/bootstrap` | JWT | Intervalos de confianza bootstrap |
| GET | `/mcnemar` | JWT | Test McNemar + Holm post-hoc |
| GET | `/cochran` | JWT | Test Cochran Q |

### Pipeline (`/api/v1/pipeline`)
| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| GET | `/status` | JWT | Progreso del pipeline (6 etapas) |
| GET | `/stages` | JWT | Info detallada por etapa |

### Reports (`/api/v1/reports`)
| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| GET | `/` | JWT | Listar reportes generados |
| POST | `/diagnosis/{id}` | JWT | Generar reporte DOCX |
| GET | `/{id}/download` | JWT | Descargar archivo |

### Users (`/api/v1/users`)
| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| GET | `/` | Admin | Listar usuarios |
| GET | `/{id}` | Admin | Detalle usuario |
| PATCH | `/{id}` | Admin | Actualizar usuario |
| DELETE | `/{id}` | Admin | Eliminar usuario |

### Health
| Método | Ruta | Auth | Descripción |
|--------|------|------|-------------|
| GET | `/health` | No | Health check |

---

## 5. DB Scripts (`scripts/`)

Scripts Node.js que operan sobre `data/vinguard.db` usando `better-sqlite3`:

```bash
npm run db:init      # Crear tablas si no existen
npm run db:reset     # Drop all tables + recreate
npm run db:seed      # Seed con 150 diagnósticos realistas
npm run db:seed:100  # Seed con 100
npm run db:seed:250  # Seed con 250
npm run db:check     # Debug: muestra estado de la DB
```

El seed crea:
- 4 usuarios (admin + 3 clientes)
- 5 modelos con métricas reales
- N diagnósticos con fechas aleatorias (últimos 30 días)
- Proporción ~25% Healthy, ~75% enfermedades

---

## 6. Modelos ML — Pipeline de Entrenamiento

```
dataset_original/ (4 clases: Healthy, Black_rot, Esca, Leaf_blight)
        │
        ▼
prepare_dataset.py → dataset/ (train/test 80/20)
        │
        ▼
preprocesamiento_aumento.py → Augmentation (rotation, flip, zoom, etc.)
        │
        ├──► train_m1_svm.py           → SVM + features clásicas
        ├──► train_m2_random_forest.py → Random Forest + features clásicas
        ├──► train_m3_knn.py           → KNN + features clásicas
        ├──► train_h1_cnn_svm.py       → CNN feature extractor + SVM
        └──► train_h2_transfer_rf.py   → MobileNetV2 transfer + RF
                │
                ▼
        comparacion_general_modelos.py → ranking_modelos.csv
                │
                ▼
        seleccion_mejor_modelo.py → H1 (CNN+SVM) es el mejor
                                    96.7% accuracy
```

---

## 7. Stack Tecnológico

| Capa | Tecnología | Versión |
|------|-----------|---------|
| ML Framework | TensorFlow / Keras | 2.13 |
| Classic ML | scikit-learn | 1.3 |
| API | FastAPI + uvicorn | 0.110 / 0.27 |
| ORM | SQLAlchemy | 2.0 |
| Auth | python-jose (JWT) + passlib (bcrypt) | — |
| Frontend (web) | Next.js 14 + React 18 | 14.2 |
| Frontend (ml) | Streamlit | 1.29 |
| Charts (web) | Recharts | 2.12 |
| State (web) | Zustand | 4.5 |
| Styling (web) | TailwindCSS + shadcn/ui | 3.4 |
| DB | SQLite (via sqlite3, SQLAlchemy, better-sqlite3) | — |
| DB Scripts | Node.js + better-sqlite3 | 22 / 11 |

---

## 8. Convenciones para IA

### Rutas de importación
- FastAPI: `backend/` es un package, se importa como `from backend.core.config import settings`
- ML: `src/` se agrega al `sys.path`, se importa como `from src.services.prediction_service import ...`
- Streamlit: igual, `src/` en `sys.path`
- Frontend: usa `@/` alias para `src/` (ej: `import api from "@/lib/api"`)

### Agregar una nueva API endpoint
1. Crear el schema en `backend/schemas/`
2. Crear/editar el router en `backend/api/`
3. Incluir el router en `backend/main.py`

### Agregar un modelo nuevo
1. Crear el training script en `src/train_*.py`
2. Agregar la key y el loader en `src/predecir_imagen.py`
3. Agregar al servicio en `src/services/prediction_service.py`
4. Agregar display name en el `mantenedor.py` o en el servicio

### Debug DB
```bash
# Terminal
cd scripts && node check-db.mjs

# Al iniciar backend
uvicorn backend.main:app --reload
# Muestra banner con users, diags, models
```

---

## 9. Estructura de Directorios

```
├── app.py                    # Streamlit entry point
├── backend/                  # FastAPI backend
│   ├── main.py
│   ├── api/                  # Routers (auth, diagnosis, models, ...)
│   ├── core/                 # Config, security
│   ├── database/             # SQLAlchemy models + engine
│   └── schemas/              # Pydantic models
├── frontend/                 # Next.js web app
│   └── src/
│       ├── app/              # Pages + layouts
│       ├── components/       # UI components (shadcn + custom)
│       ├── lib/              # API client, auth, utils
│       ├── store/            # Zustand stores
│       └── i18n/             # Translations (es/en/pt)
├── scripts/                  # Node.js DB scripts
├── database/                 # Raw SQLite repository (Streamlit)
│   └── repository.py
├── src/                      # ML training + prediction
│   ├── services/             # Shared prediction service
│   ├── predecir_imagen.py    # Core prediction engine
│   ├── mantenedor.py         # Constants
│   └── train_*.py            # Training scripts
├── ui/                       # Streamlit UI pages
│   ├── layout.py, theme.py, auth.py
│   ├── admin_dashboard.py, client_dashboard.py
│   ├── diagnosis_view.py, history_view.py
│   ├── models_view.py, pipeline_view.py
│   ├── statistics_view.py, reports_view.py
│   └── info_view.py
├── models/                   # Trained .pkl/.h5 files
├── dataset/                  # Processed train/test split
├── dataset_original/         # Raw images
├── reports/                  # Generated CSVs, plots, docs
└── data/                     # SQLite database
    └── vinguard.db
```
