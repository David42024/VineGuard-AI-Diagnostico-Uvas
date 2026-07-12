"""
optimizacion_hiperparametros.py
───────────────────────────────
Optimización de hiperparámetros para:

- M1: SVM
- M2: Random Forest
- M3: KNN
- H2: MobileNetV2 congelada + Random Forest

Metodología:
- Se utiliza únicamente el conjunto TRAIN original.
- El conjunto TEST permanece completamente aislado.
- No se aplica aumento antes de crear los folds.
- Se usa StratifiedKFold configurable.
- SVM y KNN incluyen StandardScaler dentro del Pipeline.
- H2 utiliza embeddings reales de MobileNetV2.
"""

import io
import json
import sys
import time
from pathlib import Path

import joblib
import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import tensorflow as tf

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import (
    GridSearchCV,
    ParameterGrid,
    RandomizedSearchCV,
    StratifiedKFold,
)
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC


# ─────────────────────────────────────────────
# Configuración UTF-8
# ─────────────────────────────────────────────
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
elif hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(
        sys.stdout.buffer,
        encoding="utf-8",
    )


SRC_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SRC_DIR))


from mantenedor import (
    SEED,
    TRAIN_DIR,
    TUNING_DIR,
    M1_SVM_TUNING_PATH,
    M2_RF_TUNING_PATH,
    M3_KNN_TUNING_PATH,
    H2_RF_TUNING_PATH,
    H2_EXTRACTOR_TUNING_PATH,
)
from extract_features import load_features
from preprocesamiento_h2 import (
    crear_extractor_h2,
    extraer_embeddings,
)


# ─────────────────────────────────────────────
# Configuración general
# ─────────────────────────────────────────────
N_FOLDS = 5
SCORING_PRINCIPAL = "balanced_accuracy"

# Método de búsqueda: "grid" para GridSearchCV, "random" para RandomizedSearchCV
METODO_BUSQUEDA = "grid"

# Número de iteraciones para RandomizedSearchCV (solo si METODO_BUSQUEDA = "random")
N_ITER = 20

TUNING_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


def configurar_semillas() -> None:
    """
    Configura semillas para mejorar la reproducibilidad.
    """
    np.random.seed(SEED)
    tf.random.set_seed(SEED)


def convertir_parametros_json(
    parametros: dict,
) -> str:
    """
    Convierte un diccionario de parámetros en una
    representación JSON legible para el CSV.
    """
    parametros_limpios = {}

    for clave, valor in parametros.items():
        if valor is None:
            parametros_limpios[clave] = "None"
        elif isinstance(
            valor,
            (
                np.integer,
                np.floating,
                np.bool_,
            ),
        ):
            parametros_limpios[clave] = valor.item()
        else:
            parametros_limpios[clave] = valor

    return json.dumps(
        parametros_limpios,
        ensure_ascii=False,
        sort_keys=True,
    )


def ejecutar_busqueda(
    modelo,
    param_grid,
    nombre: str,
    X: np.ndarray,
    y: np.ndarray,
    cv,
) -> tuple[GridSearchCV | RandomizedSearchCV, dict]:
    """
    Ejecuta GridSearchCV o RandomizedSearchCV y guarda los resultados.
    """
    print("\n" + "=" * 60)
    print(f"  🔍 TUNING — {nombre}")
    print("=" * 60)

    if METODO_BUSQUEDA == "random":
        total_combinaciones = len(
            list(ParameterGrid(param_grid))
        )
        n_iter_real = min(N_ITER, total_combinaciones)
        print(
            f"  Método: RandomizedSearchCV con {n_iter_real} iteraciones "
            f"(grid total: {total_combinaciones})"
        )
        search = RandomizedSearchCV(
            estimator=modelo,
            param_distributions=param_grid,
            n_iter=n_iter_real,
            scoring={
                "accuracy": "accuracy",
                "balanced_accuracy": "balanced_accuracy",
                "f1_weighted": "f1_weighted",
            },
            refit=SCORING_PRINCIPAL,
            cv=cv,
            n_jobs=-1,
            verbose=1,
            return_train_score=True,
            error_score="raise",
            random_state=SEED,
        )
    else:
        print(f"  Método: GridSearchCV")
        search = GridSearchCV(
            estimator=modelo,
            param_grid=param_grid,
            scoring={
                "accuracy": "accuracy",
                "balanced_accuracy": "balanced_accuracy",
                "f1_weighted": "f1_weighted",
            },
            refit=SCORING_PRINCIPAL,
            cv=cv,
            n_jobs=-1,
            verbose=1,
            return_train_score=True,
            error_score="raise",
        )

    inicio = time.perf_counter()

    search.fit(
        X,
        y,
    )

    tiempo_total = (
        time.perf_counter()
        - inicio
    )

    print(
        f"\n  ✅ Mejores parámetros: "
        f"{search.best_params_}"
    )

    print(
        f"  ✅ Mejor balanced accuracy CV: "
        f"{search.best_score_:.4f}"
    )

    print(
        f"  ✅ Tiempo total de búsqueda: "
        f"{tiempo_total:.2f}s"
    )

    guardar_resultados_busqueda(
        search=search,
        nombre=nombre,
    )

    mejor_indice = search.best_index_
    resultados_cv = search.cv_results_

    resumen = {
        "modelo": nombre,
        "n_folds": N_FOLDS,
        "metrica_optimizacion": SCORING_PRINCIPAL,

        "mejores_parametros": convertir_parametros_json(
            search.best_params_
        ),

        "balanced_accuracy_mean": resultados_cv[
            "mean_test_balanced_accuracy"
        ][mejor_indice],

        "balanced_accuracy_std": resultados_cv[
            "std_test_balanced_accuracy"
        ][mejor_indice],

        "accuracy_mean": resultados_cv[
            "mean_test_accuracy"
        ][mejor_indice],

        "accuracy_std": resultados_cv[
            "std_test_accuracy"
        ][mejor_indice],

        "f1_weighted_mean": resultados_cv[
            "mean_test_f1_weighted"
        ][mejor_indice],

        "f1_weighted_std": resultados_cv[
            "std_test_f1_weighted"
        ][mejor_indice],

        "train_balanced_accuracy_mean": resultados_cv[
            "mean_train_balanced_accuracy"
        ][mejor_indice],

        "diferencia_train_validacion": (
            resultados_cv[
                "mean_train_balanced_accuracy"
            ][mejor_indice]
            - resultados_cv[
                "mean_test_balanced_accuracy"
            ][mejor_indice]
        ),

        "tiempo_fit_promedio_s": resultados_cv[
            "mean_fit_time"
        ][mejor_indice],

        "tiempo_score_promedio_s": resultados_cv[
            "mean_score_time"
        ][mejor_indice],

        "tiempo_busqueda_total_s": tiempo_total,
        "n_combinaciones": len(
            resultados_cv["params"]
        ),
        "n_muestras": len(y),
        "n_features": X.shape[1],
    }

    return search, resumen


def guardar_resultados_busqueda(
    search: GridSearchCV | RandomizedSearchCV,
    nombre: str,
) -> None:
    """
    Guarda todas las combinaciones evaluadas,
    ordenadas por su ranking.
    """
    resultados = pd.DataFrame(
        search.cv_results_
    )

    columnas = [
        "rank_test_balanced_accuracy",
        "mean_test_balanced_accuracy",
        "std_test_balanced_accuracy",
        "mean_test_accuracy",
        "std_test_accuracy",
        "mean_test_f1_weighted",
        "std_test_f1_weighted",
        "mean_train_balanced_accuracy",
        "std_train_balanced_accuracy",
        "mean_fit_time",
        "std_fit_time",
        "mean_score_time",
        "std_score_time",
        "params",
    ]

    columnas_existentes = [
        columna
        for columna in columnas
        if columna in resultados.columns
    ]

    resultados = resultados[
        columnas_existentes
    ].copy()

    resultados["params"] = resultados[
        "params"
    ].apply(
        convertir_parametros_json
    )

    resultados = resultados.sort_values(
        by="rank_test_balanced_accuracy"
    )

    columnas_numericas = resultados.select_dtypes(
        include=[np.number]
    ).columns

    resultados[
        columnas_numericas
    ] = resultados[
        columnas_numericas
    ].round(6)

    nombre_archivo = (
        nombre.lower()
        .replace("—", "")
        .replace("+", "_")
        .replace(" ", "_")
        .replace("-", "_")
    )

    prefijo = (
        "randomsearch"
        if METODO_BUSQUEDA == "random"
        else "gridsearch"
    )

    resultados.to_csv(
        TUNING_DIR
        / f"{prefijo}_{nombre_archivo}.csv",
        index=False,
    )


def guardar_mejor_estimador(
    search: GridSearchCV | RandomizedSearchCV,
    nombre_archivo: str,
) -> None:
    """
    Guarda el mejor estimador reajustado sobre todo
    el conjunto train utilizado en el tuning.
    """
    ruta = (
        TUNING_DIR
        / nombre_archivo
    )

    joblib.dump(
        search.best_estimator_,
        ruta,
    )

    print(
        f"  💾 Mejor estimador guardado en: "
        f"{ruta}"
    )


# ─────────────────────────────────────────────
# Embeddings reales para H2 (usando módulo compartido)
# ─────────────────────────────────────────────


def guardar_grafico_resumen(
    df_resumen: pd.DataFrame,
) -> None:
    """
    Genera una comparación de los mejores resultados
    encontrados para cada modelo.
    """
    modelos = df_resumen[
        "modelo"
    ].tolist()

    medias = df_resumen[
        "balanced_accuracy_mean"
    ].to_numpy()

    desviaciones = df_resumen[
        "balanced_accuracy_std"
    ].to_numpy()

    figura, eje = plt.subplots(
        figsize=(11, 6)
    )

    barras = eje.bar(
        modelos,
        medias,
        yerr=desviaciones,
        capsize=5,
    )

    eje.set_ylabel(
        "Balanced accuracy promedio"
    )

    metodo_titulo = (
        "RandomizedSearchCV"
        if METODO_BUSQUEDA == "random"
        else "GridSearchCV"
    )
    eje.set_title(
        f"Mejores configuraciones obtenidas mediante {metodo_titulo}"
    )

    eje.set_ylim(
        0,
        1.02,
    )

    for barra, media in zip(
        barras,
        medias,
    ):
        eje.text(
            barra.get_x()
            + barra.get_width() / 2,
            media + 0.012,
            f"{media:.4f}",
            ha="center",
            va="bottom",
            fontsize=9,
        )

    plt.xticks(
        rotation=12
    )

    plt.tight_layout()

    figura.savefig(
        TUNING_DIR
        / "comparacion_mejores_hiperparametros.png",
        dpi=200,
        bbox_inches="tight",
    )

    plt.close(
        figura
    )


def main() -> None:
    print("=" * 60)
    print("  OPTIMIZACIÓN DE HIPERPARÁMETROS — VineGuard AI")
    print("=" * 60)

    configurar_semillas()

    if METODO_BUSQUEDA == "random":
        print(
            f"\n  Método: RandomizedSearchCV con {N_ITER} iteraciones por modelo"
        )
    else:
        print(
            f"\n  Método: GridSearchCV"
        )

    print(
        f"  Validación: StratifiedKFold "
        f"con {N_FOLDS} folds"
    )

    print(
        f"  Métrica principal: "
        f"{SCORING_PRINCIPAL}"
    )

    print(
        "  Datos utilizados: solo TRAIN original"
    )

    print(
        "  TEST permanece completamente aislado"
    )

    print(
        "  No se aplica aumento antes de los folds\n"
    )

    cv = StratifiedKFold(
        n_splits=N_FOLDS,
        shuffle=True,
        random_state=SEED,
    )

    # ─────────────────────────────────────────────
    # Cargar características clásicas
    # ─────────────────────────────────────────────
    print(
        "🔄 Cargando características clásicas "
        "del train..."
    )

    (
        X_train,
        y_train,
        _,
        _,
        _,
    ) = load_features(
        fit_scaler=False,
        augment_train=False,
        apply_scaler=False,
    )

    X_clasico = np.asarray(
        X_train,
        dtype=np.float32,
    )

    y_clasico = np.asarray(
        y_train,
        dtype=np.int32,
    )

    print(
        f"  Train clásico: {X_clasico.shape}"
    )

    resumenes = []

    # ─────────────────────────────────────────────
    # M1 — SVM
    # ─────────────────────────────────────────────
    svm_pipeline = Pipeline([
        (
            "scaler",
            StandardScaler(),
        ),
        (
            "modelo",
            SVC(
                probability=True,
                random_state=SEED,
            ),
        ),
    ])

    param_svm = [
        {
            "modelo__kernel": [
                "linear",
            ],
            "modelo__C": [
                0.1,
                1,
                10,
                100,
            ],
            "modelo__class_weight": [
                None,
                "balanced",
            ],
        },
        {
            "modelo__kernel": [
                "rbf",
            ],
            "modelo__C": [
                0.1,
                1,
                10,
                100,
            ],
            "modelo__gamma": [
                "scale",
                "auto",
                0.001,
                0.01,
            ],
            "modelo__class_weight": [
                None,
                "balanced",
            ],
        },
    ]

    gs_svm, resumen_svm = ejecutar_busqueda(
        modelo=svm_pipeline,
        param_grid=param_svm,
        nombre="M1 — SVM",
        X=X_clasico,
        y=y_clasico,
        cv=cv,
    )

    resumenes.append(
        resumen_svm
    )

    guardar_mejor_estimador(
        gs_svm,
        M1_SVM_TUNING_PATH.name,
    )

    # ─────────────────────────────────────────────
    # M2 — Random Forest
    # ─────────────────────────────────────────────
    # n_jobs=1 internamente para evitar paralelismo
    # anidado con GridSearchCV(n_jobs=-1).
    rf = RandomForestClassifier(
        random_state=SEED,
        n_jobs=1,
    )

    param_rf = {
        "n_estimators": [
            100,
            200,
        ],
        "max_depth": [
            None,
            10,
            20,
        ],
        "min_samples_split": [
            2,
            5,
        ],
        "min_samples_leaf": [
            1,
            2,
        ],
        "max_features": [
            "sqrt",
        ],
        "class_weight": [
            None,
        ],
    }

    gs_rf, resumen_rf = ejecutar_busqueda(
        modelo=rf,
        param_grid=param_rf,
        nombre="M2 — Random Forest",
        X=X_clasico,
        y=y_clasico,
        cv=cv,
    )

    resumenes.append(
        resumen_rf
    )

    guardar_mejor_estimador(
        gs_rf,
        M2_RF_TUNING_PATH.name,
    )

    # ─────────────────────────────────────────────
    # M3 — KNN
    # ─────────────────────────────────────────────
    knn_pipeline = Pipeline([
        (
            "scaler",
            StandardScaler(),
        ),
        (
            "modelo",
            KNeighborsClassifier(
                n_jobs=-1,
            ),
        ),
    ])

    param_knn = {
        "modelo__n_neighbors": [
            3,
            5,
            7,
        ],
        "modelo__weights": [
            "uniform",
            "distance",
        ],
        "modelo__metric": [
            "euclidean",
            "manhattan",
        ],
        "modelo__algorithm": [
            "auto",
        ],
    }

    gs_knn, resumen_knn = ejecutar_busqueda(
        modelo=knn_pipeline,
        param_grid=param_knn,
        nombre="M3 — KNN",
        X=X_clasico,
        y=y_clasico,
        cv=cv,
    )

    resumenes.append(
        resumen_knn
    )

    guardar_mejor_estimador(
        gs_knn,
        M3_KNN_TUNING_PATH.name,
    )

    # ─────────────────────────────────────────────
    # H2 — MobileNetV2 + Random Forest
    # ─────────────────────────────────────────────
    # Crear y guardar extractor una sola vez
    extractor_h2 = crear_extractor_h2()
    extractor_ruta = H2_EXTRACTOR_TUNING_PATH
    extractor_h2.save(extractor_ruta)
    print(f"\n💾 Extractor MobileNetV2 guardado en: {extractor_ruta}")
    
    X_h2, y_h2 = extraer_embeddings(TRAIN_DIR, extractor_h2)

    rf_h2 = RandomForestClassifier(
        random_state=SEED,
        n_jobs=1,
    )

    param_h2 = {
        "n_estimators": [
            100,
            200,
        ],
        "max_depth": [
            None,
            10,
            20,
        ],
        "min_samples_split": [
            2,
            5,
        ],
        "min_samples_leaf": [
            1,
            2,
        ],
        "max_features": [
            "sqrt",
        ],
        "class_weight": [
            None,
        ],
    }

    gs_h2, resumen_h2 = ejecutar_busqueda(
        modelo=rf_h2,
        param_grid=param_h2,
        nombre="H2 — MobileNetV2 + Random Forest",
        X=X_h2,
        y=y_h2,
        cv=cv,
    )

    resumenes.append(
        resumen_h2
    )

    guardar_mejor_estimador(
        gs_h2,
        H2_RF_TUNING_PATH.name,
    )

    # ─────────────────────────────────────────────
    # Resumen final
    # ─────────────────────────────────────────────
    df_resumen = pd.DataFrame(
        resumenes
    )

    columnas_numericas = df_resumen.select_dtypes(
        include=[np.number]
    ).columns

    df_resumen[
        columnas_numericas
    ] = df_resumen[
        columnas_numericas
    ].round(6)

    df_resumen = df_resumen.sort_values(
        by="balanced_accuracy_mean",
        ascending=False,
    )

    ruta_resumen = (
        TUNING_DIR
        / "mejores_hiperparametros.csv"
    )

    df_resumen.to_csv(
        ruta_resumen,
        index=False,
    )

    guardar_grafico_resumen(
        df_resumen
    )

    print("\n" + "=" * 60)
    print("  MEJORES HIPERPARÁMETROS ENCONTRADOS")
    print("=" * 60)

    columnas_mostrar = [
        "modelo",
        "balanced_accuracy_mean",
        "balanced_accuracy_std",
        "accuracy_mean",
        "f1_weighted_mean",
        "diferencia_train_validacion",
        "n_combinaciones",
        "tiempo_busqueda_total_s",
        "mejores_parametros",
    ]

    print(
        df_resumen[
            columnas_mostrar
        ].to_string(
            index=False
        )
    )

    print(
        f"\n✅ Resumen guardado en: "
        f"{ruta_resumen}"
    )

    print(
        f"✅ Resultados detallados guardados en: "
        f"{TUNING_DIR}"
    )

    print(
        f"✅ Gráfico guardado en: "
        f"{TUNING_DIR / 'comparacion_mejores_hiperparametros.png'}"
    )

    print(
        "\n⚠️ H1 — CNN + SVM no se incluye en este proceso. "
        "El ajuste completo de la CNN para cada combinación y fold "
        "tendría un costo computacional elevado. El SVM podría "
        "optimizarse por separado usando embeddings de la CNN congelada."
    )

    print("\n✅ Optimización completada.")


if __name__ == "__main__":
    main()