"""
cross_validation_modelos.py

Validación cruzada estratificada de 5 folds para:
- M1: SVM
- M2: Random Forest
- M3: KNN

El conjunto test se mantiene completamente aislado.
La validación cruzada utiliza únicamente las imágenes reales
del conjunto de entrenamiento, sin aumento previo a los folds.
"""

import io
import sys
import time
import warnings
from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from sklearn.base import clone
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    f1_score,
    matthews_corrcoef,
    precision_score,
    recall_score,
)
from sklearn.model_selection import StratifiedKFold
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
elif hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(
        sys.stdout.buffer,
        encoding="utf-8",
    )


warnings.filterwarnings("ignore")

SRC_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SRC_DIR))

from mantenedor import (
    COMPARATIVOS_DIR,
    CROSS_VALIDATION_DIR,
    CROSS_VALIDATION_RESULTADOS_PATH,
    SEED,
)
from extract_features import load_features


N_FOLDS = 5


def ejecutar_cv(
    modelo,
    nombre: str,
    X: np.ndarray,
    y: np.ndarray,
) -> tuple[dict, list[dict]]:
    """
    Ejecuta StratifiedKFold y devuelve:
    - resumen del modelo;
    - resultados individuales de cada fold.
    """
    skf = StratifiedKFold(
        n_splits=N_FOLDS,
        shuffle=True,
        random_state=SEED,
    )

    resultados_folds = []

    print(f"\n🔹 {nombre}")

    for fold, (train_idx, val_idx) in enumerate(
        skf.split(X, y),
        start=1,
    ):
        X_train_fold = X[train_idx]
        X_val_fold = X[val_idx]

        y_train_fold = y[train_idx]
        y_val_fold = y[val_idx]

        # Modelo independiente en cada fold
        clasificador = clone(modelo)

        inicio_entrenamiento = time.perf_counter()

        clasificador.fit(
            X_train_fold,
            y_train_fold,
        )

        tiempo_entrenamiento = (
            time.perf_counter()
            - inicio_entrenamiento
        )

        inicio_inferencia = time.perf_counter()

        y_pred = clasificador.predict(
            X_val_fold
        )

        tiempo_inferencia = (
            time.perf_counter()
            - inicio_inferencia
        )

        resultado_fold = {
            "modelo": nombre,
            "fold": fold,
            "n_train": len(train_idx),
            "n_validacion": len(val_idx),

            "accuracy": accuracy_score(
                y_val_fold,
                y_pred,
            ),

            "balanced_accuracy": balanced_accuracy_score(
                y_val_fold,
                y_pred,
            ),

            "precision_weighted": precision_score(
                y_val_fold,
                y_pred,
                average="weighted",
                zero_division=0,
            ),

            "recall_weighted": recall_score(
                y_val_fold,
                y_pred,
                average="weighted",
                zero_division=0,
            ),

            "f1_weighted": f1_score(
                y_val_fold,
                y_pred,
                average="weighted",
                zero_division=0,
            ),

            "mcc": matthews_corrcoef(
                y_val_fold,
                y_pred,
            ),

            "tiempo_entrenamiento_s": (
                tiempo_entrenamiento
            ),

            "tiempo_inferencia_total_s": (
                tiempo_inferencia
            ),

            "tiempo_inferencia_ms_muestra": (
                tiempo_inferencia
                / len(y_pred)
            ) * 1000,
        }

        resultados_folds.append(
            resultado_fold
        )

        print(
            f"   Fold {fold}/{N_FOLDS} — "
            f"Acc: {resultado_fold['accuracy']:.4f}, "
            f"Bal. Acc: "
            f"{resultado_fold['balanced_accuracy']:.4f}, "
            f"F1: {resultado_fold['f1_weighted']:.4f}, "
            f"MCC: {resultado_fold['mcc']:.4f}"
        )

    df_folds = pd.DataFrame(
        resultados_folds
    )

    resumen = {
        "modelo": nombre,
        "n_folds": N_FOLDS,

        "accuracy_mean": df_folds[
            "accuracy"
        ].mean(),
        "accuracy_std": df_folds[
            "accuracy"
        ].std(ddof=1),

        "balanced_accuracy_mean": df_folds[
            "balanced_accuracy"
        ].mean(),
        "balanced_accuracy_std": df_folds[
            "balanced_accuracy"
        ].std(ddof=1),

        "precision_mean": df_folds[
            "precision_weighted"
        ].mean(),
        "precision_std": df_folds[
            "precision_weighted"
        ].std(ddof=1),

        "recall_mean": df_folds[
            "recall_weighted"
        ].mean(),
        "recall_std": df_folds[
            "recall_weighted"
        ].std(ddof=1),

        "f1_mean": df_folds[
            "f1_weighted"
        ].mean(),
        "f1_std": df_folds[
            "f1_weighted"
        ].std(ddof=1),

        "mcc_mean": df_folds[
            "mcc"
        ].mean(),
        "mcc_std": df_folds[
            "mcc"
        ].std(ddof=1),

        "tiempo_entrenamiento_mean_s": df_folds[
            "tiempo_entrenamiento_s"
        ].mean(),

        "tiempo_inferencia_mean_ms": df_folds[
            "tiempo_inferencia_ms_muestra"
        ].mean(),
    }

    return resumen, resultados_folds


def guardar_grafico(
    df_resumen: pd.DataFrame,
) -> None:
    """
    Guarda la comparación de accuracy promedio.
    """
    modelos = df_resumen[
        "modelo"
    ].tolist()

    medias = df_resumen[
        "accuracy_mean"
    ].to_numpy()

    desviaciones = df_resumen[
        "accuracy_std"
    ].to_numpy()

    figura, eje = plt.subplots(
        figsize=(10, 5)
    )

    barras = eje.bar(
        modelos,
        medias,
        yerr=desviaciones,
        capsize=5,
    )

    eje.set_ylabel(
        "Accuracy promedio"
    )

    eje.set_title(
        "Validación cruzada estratificada de 5 folds"
    )

    eje.set_ylim(
        0,
        1,
    )

    for barra, media in zip(
        barras,
        medias,
    ):
        eje.text(
            barra.get_x()
            + barra.get_width() / 2,
            media + 0.015,
            f"{media:.4f}",
            ha="center",
            va="bottom",
            fontsize=9,
        )

    plt.xticks(
        rotation=15
    )

    plt.tight_layout()

    figura.savefig(
        CROSS_VALIDATION_DIR
        / "cross_validation_comparacion.png",
        dpi=200,
        bbox_inches="tight",
    )

    plt.close(
        figura
    )


def main() -> None:
    print("=" * 60)
    print("  VALIDACIÓN CRUZADA — VineGuard AI")
    print("=" * 60)

    print(
        f"\n  StratifiedKFold con "
        f"{N_FOLDS} folds"
    )

    print(
        "  Se utiliza únicamente el train original."
    )

    print(
        "  El conjunto test permanece aislado."
    )

    print(
        "  No se aplica aumento antes de crear los folds.\n"
    )

    COMPARATIVOS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    CROSS_VALIDATION_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # Importante:
    # características reales de train, sin aumento
    # y sin escalado global.
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

    X = np.asarray(
        X_train,
        dtype=np.float32,
    )

    y = np.asarray(
        y_train,
        dtype=np.int32,
    )

    print(
        f"  Muestras utilizadas: {len(y)}"
    )

    print(
        f"  Características: {X.shape[1]}"
    )

    modelos = [
        (
            "M1 — SVM",
            Pipeline([
                (
                    "scaler",
                    StandardScaler(),
                ),
                (
                    "modelo",
                    SVC(
                        kernel="rbf",
                        C=10.0,
                        gamma="scale",
                        probability=False,
                        class_weight="balanced",
                        random_state=SEED,
                    ),
                ),
            ]),
        ),
        (
            "M2 — Random Forest",
            RandomForestClassifier(
                n_estimators=200,
                max_depth=None,
                min_samples_split=2,
                min_samples_leaf=1,
                class_weight=None,
                n_jobs=-1,
                random_state=SEED,
            ),
        ),
        (
            "M3 — KNN",
            Pipeline([
                (
                    "scaler",
                    StandardScaler(),
                ),
                (
                    "modelo",
                    KNeighborsClassifier(
                        n_neighbors=5,
                        metric="euclidean",
                        weights="distance",
                        algorithm="auto",
                        n_jobs=-1,
                    ),
                ),
            ]),
        ),
    ]

    resumenes = []
    todos_los_folds = []

    for nombre, modelo in modelos:
        resumen, resultados_folds = ejecutar_cv(
            modelo,
            nombre,
            X,
            y,
        )

        resumenes.append(
            resumen
        )

        todos_los_folds.extend(
            resultados_folds
        )

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
    ].round(4)

    df_folds = pd.DataFrame(
        todos_los_folds
    )

    columnas_folds = df_folds.select_dtypes(
        include=[np.number]
    ).columns

    df_folds[
        columnas_folds
    ] = df_folds[
        columnas_folds
    ].round(4)

    ruta_resumen = CROSS_VALIDATION_RESULTADOS_PATH

    ruta_folds = (
        CROSS_VALIDATION_DIR
        / "cross_validation_por_fold.csv"
    )

    df_resumen.to_csv(
        ruta_resumen,
        index=False,
    )

    df_folds.to_csv(
        ruta_folds,
        index=False,
    )

    guardar_grafico(
        df_resumen
    )

    print("\n" + "=" * 60)
    print("  RESUMEN CROSS-VALIDATION")
    print("=" * 60)

    print(
        df_resumen.to_string(
            index=False
        )
    )

    print(
        f"\n✅ Resumen guardado en: "
        f"{ruta_resumen}"
    )

    print(
        f"✅ Resultados por fold guardados en: "
        f"{ruta_folds}"
    )

    print(
        f"✅ Gráfico guardado en: "
        f"{CROSS_VALIDATION_DIR / 'cross_validation_comparacion.png'}"
    )

    print(
        "\n⚠️ H1 y H2 no se incluyen en este script "
        "hasta ejecutar su validación cruzada real."
    )


if __name__ == "__main__":
    main()