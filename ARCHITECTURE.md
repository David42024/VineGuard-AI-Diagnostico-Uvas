# VineGuard AI — Arquitectura del Sistema

> Plataforma inteligente para el diagnóstico de enfermedades en hojas de vid mediante modelos clásicos, modelos híbridos y redes neuronales, con un laboratorio técnico en Streamlit, una API central en FastAPI y una aplicación web en Next.js.

---

## 1. Objetivo de la arquitectura

VineGuard AI separa claramente tres responsabilidades:

- **Streamlit AI Lab:** ejecución y visualización del pipeline de inteligencia artificial.
- **FastAPI:** autenticación, diagnósticos, acceso a modelos, estadísticas y reportes.
- **Next.js:** interfaz web final para administradores y clientes.

La arquitectura evita duplicar la lógica de predicción y mantiene separados los datos operativos de la aplicación y los artefactos generados por Machine Learning.

---

## 2. Vista general

```text
                          ┌──────────────────────────┐
                          │     Streamlit AI Lab     │
                          │ EDA, entrenamiento, CV,  │
                          │ tuning y estadística     │
                          └────────────┬─────────────┘
                                       │
                                       │ Python
                                       ▼
┌───────────────────┐        ┌───────────────────────┐
│ dataset_original/ │───────►│   Pipeline de ML      │
└───────────────────┘        │  modelos y resultados │
                             └────────────┬──────────┘
                                          │
                          ┌───────────────┴────────────────┐
                          ▼                                ▼
                ┌──────────────────┐             ┌──────────────────┐
                │     models/      │             │     reports/     │
                │ .h5, .pkl        │             │ CSV, PNG, DOCX   │
                └────────┬─────────┘             └────────┬─────────┘
                         │                                │
                         └───────────────┬────────────────┘
                                         ▼
                              ┌─────────────────────┐
                              │       FastAPI       │
                              │ Auth, diagnóstico,  │
                              │ modelos y reportes  │
                              └──────────┬──────────┘
                                         │
                                         │ HTTP / JSON
                                         ▼
                              ┌─────────────────────┐
                              │ Next.js + React     │
                              │ Aplicación final    │
                              └─────────────────────┘

                              ┌─────────────────────┐
                              │ SQLite              │
                              │ users, diagnostics, │
                              │ audit_log           │
                              └─────────────────────┘
```

---

## 3. Responsabilidad de cada componente

## 3.1 Streamlit AI Lab

Streamlit funciona como el módulo técnico y experimental del sistema.

### Funciones principales

- Lectura y validación del dataset.
- Análisis exploratorio de datos.
- Preprocesamiento y aumento de imágenes.
- Entrenamiento de modelos.
- Validación cruzada configurable.
- Optimización de hiperparámetros.
- Pruebas estadísticas robustas.
- Comparación y selección del mejor modelo.
- Visualización de matrices de confusión, curvas ROC y métricas.
- Generación y descarga de reportes técnicos.
- Verificación de artefactos `.h5` y `.pkl`.

### Directorios utilizados

```text
dataset_original/
dataset/
models/
reports/
```

### Archivos principales

| Archivo | Responsabilidad |
|---|---|
| `app.py` | Punto de entrada, sesión, navegación y control de acceso |
| `ui/auth.py` | Inicio de sesión y validación |
| `ui/layout.py` | Sidebar, encabezado y navegación |
| `ui/theme.py` | Tema claro/oscuro |
| `ui/admin_dashboard.py` | Resumen ejecutivo |
| `ui/client_dashboard.py` | Inicio del cliente |
| `ui/diagnosis_view.py` | Diagnóstico de imágenes |
| `ui/history_view.py` | Historial |
| `ui/models_view.py` | Estado y métricas de modelos |
| `ui/pipeline_view.py` | Estado del pipeline |
| `ui/statistics_view.py` | Resultados estadísticos |
| `ui/reports_view.py` | Reportes generados |
| `ui/components.py` | Componentes reutilizables |

---

## 3.2 FastAPI

FastAPI es el núcleo operativo del sistema y el único punto de acceso para el frontend Next.js.

### Funciones principales

- Autenticación y autorización mediante JWT.
- Gestión de usuarios.
- Diagnóstico de imágenes.
- Carga y uso de modelos entrenados.
- Consulta del ranking de modelos.
- Consulta de estadísticas y resultados del pipeline.
- Gestión de reportes.
- Registro de diagnósticos.
- Registro de auditoría.
- Exposición de datos en formato JSON.

### Regla principal

Next.js no debe leer directamente SQLite, CSV, `.h5` ni `.pkl`.

```text
Next.js → FastAPI → SQLite / models / reports
```

### Archivos principales

| Archivo | Responsabilidad |
|---|---|
| `backend/main.py` | Creación de la API, CORS y manejo de errores |
| `backend/core/config.py` | Variables de entorno y configuración |
| `backend/core/security.py` | JWT y hashing de contraseñas |
| `backend/database/database.py` | Conexión ORM a SQLite |
| `backend/api/auth.py` | Login, logout, refresh y usuario actual |
| `backend/api/diagnosis.py` | Crear y consultar diagnósticos |
| `backend/api/models.py` | Estado, ranking y mejor modelo |
| `backend/api/pipeline.py` | Estado del pipeline |
| `backend/api/statistics.py` | Estadísticas, CV y pruebas |
| `backend/api/reports.py` | Generación y descarga de reportes |
| `backend/api/users.py` | Gestión de usuarios |
| `backend/schemas/` | Esquemas Pydantic |

---

## 3.3 Next.js

Next.js es la aplicación web final orientada a administradores y clientes.

### Funciones del cliente

- Iniciar sesión.
- Subir una imagen.
- Ejecutar un diagnóstico.
- Consultar confianza y probabilidades.
- Revisar historial.
- Consultar información de enfermedades.
- Descargar reportes.
- Usar chatbot por texto y voz.
- Cambiar idioma.
- Cambiar tema.

### Funciones del administrador

- Ver dashboard general.
- Consultar diagnósticos.
- Consultar usuarios.
- Revisar ranking de modelos.
- Revisar estado del pipeline.
- Consultar estadísticas.
- Descargar reportes.

### Archivos principales

| Archivo | Responsabilidad |
|---|---|
| `src/middleware.ts` | Protección de rutas |
| `src/app/layout.tsx` | Layout raíz |
| `src/app/(admin)/layout.tsx` | Layout administrativo |
| `src/app/(admin)/admin/page.tsx` | Dashboard administrativo |
| `src/app/(admin)/admin/models/page.tsx` | Modelos |
| `src/app/(admin)/admin/pipeline/page.tsx` | Pipeline |
| `src/app/(admin)/admin/statistics/page.tsx` | Estadísticas |
| `src/app/(admin)/admin/reports/page.tsx` | Reportes |
| `src/app/(admin)/admin/users/page.tsx` | Usuarios |
| `src/app/(client)/dashboard/page.tsx` | Inicio del cliente |
| `src/app/(client)/dashboard/diagnosis/page.tsx` | Diagnóstico |
| `src/app/(client)/dashboard/history/page.tsx` | Historial |
| `src/components/layout/` | Sidebar, header y AppShell |
| `src/components/dashboard/` | Tarjetas y métricas |
| `src/lib/api.ts` | Cliente Axios |
| `src/lib/auth.ts` | Gestión de sesión |
| `src/store/` | Estado global con Zustand |
| `src/i18n/` | Traducciones español/inglés |

---

## 4. Persistencia

VineGuard AI utiliza dos mecanismos de persistencia separados.

## 4.1 SQLite: datos operativos

Archivo:

```text
data/vinguard.db
```

Tablas principales:

| Tabla | Contenido |
|---|---|
| `users` | Cuentas, roles, hashes de contraseñas y último acceso |
| `diagnostics` | Resultado, confianza, modelo usado, archivo y fecha |
| `audit_log` | Accesos y acciones realizadas |
| `models` | Metadatos básicos opcionales de modelos |

SQLite no guarda los pesos entrenados ni los resultados completos del pipeline.

## 4.2 Archivos del pipeline ML

| Ruta | Contenido |
|---|---|
| `models/*.pkl` | SVM, Random Forest, KNN y clasificadores híbridos |
| `models/*.h5` | Extractores CNN y modelos Keras |
| `reports/modelos/ranking_modelos.csv` | Ranking final |
| `reports/modelos/*/resultados_*.csv` | Métricas por modelo |
| `reports/modelos/cross_validation/` | Resultados de validación cruzada |
| `reports/modelos/tuning/` | Mejores hiperparámetros |
| `reports/estadistica/` | McNemar, Cochran-Q, Bootstrap y tamaños de efecto |
| `reports/eda/` | Análisis exploratorio |
| `reports/preprocessing/` | Ejemplos de aumento |
| `reports/modelos/*.png` | Matrices de confusión y curvas ROC |

### Fuente de verdad

Los archivos persistidos son la fuente real de los resultados.

`st.session_state` solo actúa como caché temporal de interfaz.

```text
ranking_modelos.csv
        ↓
Streamlit lo carga
        ↓
st.session_state.ranking_data
```

Si la sesión termina, los datos se recuperan nuevamente desde los archivos.

---

## 5. Modelos de Machine Learning

| Key | Modelo | Tipo | Artefactos |
|---|---|---|---|
| `M1` | SVM | Clásico | `svm_model.pkl`, `svm_scaler.pkl` |
| `M2` | Random Forest | Clásico | `random_forest_model.pkl` |
| `M3` | KNN | Clásico | `knn_model.pkl`, `knn_scaler.pkl` |
| `H1` | CNN + SVM | Híbrido | `cnn_feature_extractor.h5`, `h1_svm_classifier.pkl` |
| `H2` | MobileNetV2 + RF | Híbrido | `transfer_feature_extractor.h5`, `transfer_random_forest_model.pkl` |

El modelo H1 no se representa únicamente mediante un archivo `.h5`. Su pipeline completo está formado por:

```text
Extractor CNN (.h5) + Clasificador SVM (.pkl)
```

FastAPI carga ambos artefactos como una sola unidad de inferencia.

---

## 6. Pipeline de entrenamiento

```text
1. Preparación del dataset
2. EDA
3. Preprocesamiento y aumento
4. Entrenamiento de modelos
5. Validación cruzada
6. Optimización de hiperparámetros
7. Pruebas estadísticas
8. Comparación de modelos
9. Selección del mejor modelo
10. Persistencia de artefactos
```

### Flujo

```text
dataset_original/
        │
        ▼
prepare_dataset.py
        │
        ▼
dataset/train + dataset/test
        │
        ▼
preprocesamiento_aumento.py
        │
        ├── train_m1_svm.py
        ├── train_m2_random_forest.py
        ├── train_m3_knn.py
        ├── train_h1_cnn_svm.py
        └── train_h2_transfer_random_forest.py
        │
        ▼
cross_validation_modelos.py
        │
        ▼
optimizacion_hiperparametros.py
        │
        ▼
validacion_estadistica_modelos.py
        │
        ▼
evaluacion_comparativa.py
        │
        ▼
seleccion_mejor_modelo.py
        │
        ├── reports/modelos/ranking_modelos.csv
        └── reports/modelos/mejor_modelo.json
```

---

## 7. Servicios compartidos

Para evitar duplicar lógica entre Streamlit y FastAPI, se centralizan dos servicios.

## 7.1 Servicio de predicción

Archivo:

```text
src/services/prediction_service.py
```

Responsabilidades:

```python
load_single_model(model_key)
load_all_models()
predict_from_image(image, model_key)
predict_consensus(image)
get_best_model()
```

## 7.2 Servicio de resultados

Archivo recomendado:

```text
src/services/results_service.py
```

Responsabilidades:

```python
load_model_ranking()
load_best_model()
load_cross_validation_results()
load_tuning_results()
load_statistical_results()
get_pipeline_status()
```

---

## 8. Archivo del mejor modelo

Además del ranking CSV, se recomienda mantener:

```text
reports/modelos/mejor_modelo.json
```

Ejemplo:

```json
{
  "key": "H1",
  "name": "CNN+SVM",
  "accuracy": 0.9890,
  "f1_macro": 0.9912,
  "mcc": 0.9847,
  "artifacts": [
    "models/cnn_feature_extractor.h5",
    "models/h1_svm_classifier.pkl"
  ]
}
```

Este archivo facilita que FastAPI identifique el modelo seleccionado sin tener que interpretar el ranking completo en cada solicitud.

---

## 9. Flujo de diagnóstico

```text
Usuario sube una imagen
        │
        ▼
Next.js envía FormData
        │
        ▼
POST /api/v1/diagnoses
        │
        ▼
FastAPI valida JWT
        │
        ▼
FastAPI identifica el modelo
        │
        ▼
prediction_service carga .h5/.pkl
        │
        ▼
Se realiza la inferencia
        │
        ▼
El resultado se guarda en SQLite
        │
        ▼
FastAPI devuelve JSON
        │
        ▼
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

## 10. Flujo de autenticación

```text
Next.js
  POST /api/v1/auth/login
        │
        ▼
FastAPI consulta users en SQLite
        │
        ▼
Valida contraseña
        │
        ▼
Genera JWT
        │
        ▼
Devuelve access_token + usuario
        │
        ▼
Next.js guarda sesión y rol
```

---

## 11. Endpoints principales

### Autenticación

| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/api/v1/auth/login` | Iniciar sesión |
| `POST` | `/api/v1/auth/logout` | Cerrar sesión |
| `POST` | `/api/v1/auth/refresh` | Renovar token |
| `GET` | `/api/v1/auth/me` | Usuario actual |

### Diagnósticos

| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/api/v1/diagnoses` | Crear diagnóstico |
| `GET` | `/api/v1/diagnoses` | Listar diagnósticos |
| `GET` | `/api/v1/diagnoses/{id}` | Obtener detalle |
| `DELETE` | `/api/v1/diagnoses/{id}` | Eliminar diagnóstico |
| `POST` | `/api/v1/diagnoses/{id}/repeat` | Repetir diagnóstico |

### Modelos

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/api/v1/models` | Listar modelos |
| `GET` | `/api/v1/models/ranking` | Obtener ranking |
| `GET` | `/api/v1/models/best` | Obtener mejor modelo |
| `POST` | `/api/v1/models/test` | Probar un modelo |

### Pipeline y estadísticas

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/api/v1/pipeline/status` | Estado general |
| `GET` | `/api/v1/pipeline/stages` | Estado por etapa |
| `GET` | `/api/v1/statistics/summary` | Resumen |
| `GET` | `/api/v1/statistics/cross-validation` | Validación cruzada |
| `GET` | `/api/v1/statistics/bootstrap` | Bootstrap |
| `GET` | `/api/v1/statistics/mcnemar` | McNemar |
| `GET` | `/api/v1/statistics/cochran` | Cochran-Q |

### Reportes y usuarios

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/api/v1/reports` | Listar reportes |
| `POST` | `/api/v1/reports/diagnosis/{id}` | Generar reporte |
| `GET` | `/api/v1/reports/{id}/download` | Descargar reporte |
| `GET` | `/api/v1/users` | Listar usuarios |
| `PATCH` | `/api/v1/users/{id}` | Actualizar usuario |
| `DELETE` | `/api/v1/users/{id}` | Eliminar usuario |

---

## 12. Bilingüe, tema y chatbot

### Bilingüe

- Streamlit: diccionarios Python y `st.session_state`.
- Next.js: archivos `src/i18n/es.json` y `src/i18n/en.json`.

### Modo claro/oscuro

- Streamlit: variables CSS centralizadas en `ui/theme.py`.
- Next.js: Tailwind CSS, variables semánticas y Zustand.

### Chatbot

El chatbot se implementa principalmente en Next.js.

Funciones:

- Entrada de texto.
- Reconocimiento de voz desde el navegador.
- Síntesis de voz.
- Preguntas frecuentes.
- Ayuda sobre diagnósticos.
- Explicación de resultados.

Endpoint recomendado:

```text
POST /api/v1/chat
```

---

## 13. Despliegue

| Componente | Plataforma |
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

Variable de entorno:

```env
NEXT_PUBLIC_API_URL=https://vinguard-api.onrender.com/api/v1
```

### Persistencia de SQLite

SQLite requiere un disco persistente en Render.

Ruta recomendada:

```text
/var/data/vinguard.db
```

Ejemplo:

```env
DATABASE_URL=sqlite:////var/data/vinguard.db
```

---

## 14. Backups

Para respaldar el sistema se deben conservar:

```text
data/vinguard.db
models/
reports/
```

- `vinguard.db`: usuarios, diagnósticos y auditoría.
- `models/`: artefactos entrenados.
- `reports/`: métricas, gráficos y resultados.

Si se eliminan `models/` o `reports/`, se pierde el resultado del pipeline aunque SQLite siga intacto.

---

## 15. Estructura del proyecto

```text
├── app.py
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
│   │   ├── prediction_service.py
│   │   └── results_service.py
│   ├── mantenedor.py
│   ├── predecir_imagen.py
│   ├── train_m1_svm.py
│   ├── train_m2_random_forest.py
│   ├── train_m3_knn.py
│   ├── train_h1_cnn_svm.py
│   ├── train_h2_transfer_random_forest.py
│   ├── cross_validation_modelos.py
│   ├── optimizacion_hiperparametros.py
│   ├── validacion_estadistica_modelos.py
│   ├── evaluacion_comparativa.py
│   └── seleccion_mejor_modelo.py
├── ui/
├── data/
│   └── vinguard.db
├── models/
├── reports/
├── dataset/
└── dataset_original/
```

---

## 16. Decisiones de arquitectura

- SQLite se mantiene para los datos operativos.
- Los modelos no se almacenan en SQLite.
- Los resultados del pipeline permanecen en archivos.
- Streamlit se usa como laboratorio técnico.
- Next.js se usa como aplicación final.
- FastAPI centraliza el acceso a datos y modelos.
- Next.js nunca accede directamente a SQLite ni al sistema de archivos.
- La lógica de predicción se comparte mediante `prediction_service.py`.
- La lectura de resultados se comparte mediante `results_service.py`.
- `st.session_state` se usa solo como caché temporal.
- No se requiere una migración a PostgreSQL para la versión académica.

---

## 17. Orden de trabajo

1. Consolidar las vistas y funciones de Streamlit.
2. Centralizar rutas, predicción y lectura de resultados.
3. Completar endpoints de FastAPI.
4. Integrar Next.js con FastAPI.
5. Implementar bilingüe, tema y chatbot.
6. Ejecutar pruebas integrales.
7. Desplegar Streamlit y FastAPI en Render.
8. Desplegar Next.js en Vercel.
9. Registrar tareas, evidencias y pruebas en Jira.