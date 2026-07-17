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
    M1_SVM_KERNEL,
    M1_SVM_C,
    M1_SVM_GAMMA,
    M1_SVM_CLASS_WEIGHT,
    M2_RF_N_ESTIMATORS,
    M2_RF_MAX_DEPTH,
    M2_RF_MIN_SAMPLES_SPLIT,
    M2_RF_MIN_SAMPLES_LEAF,
    M2_RF_CLASS_WEIGHT,
    M3_KNN_N_NEIGHBORS,
    M3_KNN_METRIC,
    M3_KNN_WEIGHTS,
    M3_KNN_ALGORITHM,
    M3_KNN_P,
    SEED,
)
from extract_features import load_features


N_FOLDS = 5


def _fold_summary_line(fold: int, total: int, metrics: dict) -> str:
    return (
        f"   Fold {fold}/{total} — "
        f"Acc: {metrics['accuracy']:.4f}, "
        f"F1-macro: {metrics['f1_macro']:.4f}, "
        f"MCC: {metrics['mcc']:.4f}"
    )


def ejecutar_cv(
    modelo,
    nombre: str,
    X: np.ndarray,
    y: np.ndarray,
) -> tuple[dict, list[dict]]:
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

        clasificador = clone(modelo)

        inicio_entrenamiento = time.perf_counter()
        clasificador.fit(X_train_fold, y_train_fold)
        tiempo_entrenamiento = time.perf_counter() - inicio_entrenamiento

        inicio_inferencia = time.perf_counter()
        y_pred = clasificador.predict(X_val_fold)
        tiempo_inferencia = time.perf_counter() - inicio_inferencia

        resultado_fold = {
            "modelo": nombre,
            "fold": fold,
            "n_train": len(train_idx),
            "n_validacion": len(val_idx),
            "accuracy": accuracy_score(y_val_fold, y_pred),
            "balanced_accuracy": balanced_accuracy_score(y_val_fold, y_pred),
            "precision_weighted": precision_score(y_val_fold, y_pred, average="weighted", zero_division=0),
            "recall_weighted": recall_score(y_val_fold, y_pred, average="weighted", zero_division=0),
            "f1_weighted": f1_score(y_val_fold, y_pred, average="weighted", zero_division=0),
            "precision_macro": precision_score(y_val_fold, y_pred, average="macro", zero_division=0),
            "recall_macro": recall_score(y_val_fold, y_pred, average="macro", zero_division=0),
            "f1_macro": f1_score(y_val_fold, y_pred, average="macro", zero_division=0),
            "mcc": matthews_corrcoef(y_val_fold, y_pred),
            "tiempo_entrenamiento_s": tiempo_entrenamiento,
            "tiempo_inferencia_total_s": tiempo_inferencia,
            "tiempo_inferencia_ms_muestra": (tiempo_inferencia / len(y_pred)) * 1000,
        }

        resultados_folds.append(resultado_fold)
        print(_fold_summary_line(fold, N_FOLDS, resultado_fold))

    df_folds = pd.DataFrame(resultados_folds)

    resumen = {
        "modelo": nombre,
        "n_folds": N_FOLDS,
        "accuracy_mean": df_folds["accuracy"].mean(),
        "accuracy_std": df_folds["accuracy"].std(ddof=1),
        "balanced_accuracy_mean": df_folds["balanced_accuracy"].mean(),
        "balanced_accuracy_std": df_folds["balanced_accuracy"].std(ddof=1),
        "precision_weighted_mean": df_folds["precision_weighted"].mean(),
        "precision_weighted_std": df_folds["precision_weighted"].std(ddof=1),
        "recall_weighted_mean": df_folds["recall_weighted"].mean(),
        "recall_weighted_std": df_folds["recall_weighted"].std(ddof=1),
        "f1_weighted_mean": df_folds["f1_weighted"].mean(),
        "f1_weighted_std": df_folds["f1_weighted"].std(ddof=1),
        "precision_macro_mean": df_folds["precision_macro"].mean(),
        "precision_macro_std": df_folds["precision_macro"].std(ddof=1),
        "recall_macro_mean": df_folds["recall_macro"].mean(),
        "recall_macro_std": df_folds["recall_macro"].std(ddof=1),
        "f1_macro_mean": df_folds["f1_macro"].mean(),
        "f1_macro_std": df_folds["f1_macro"].std(ddof=1),
        "mcc_mean": df_folds["mcc"].mean(),
        "mcc_std": df_folds["mcc"].std(ddof=1),
        "tiempo_entrenamiento_mean_s": df_folds["tiempo_entrenamiento_s"].mean(),
        "tiempo_inferencia_mean_ms": df_folds["tiempo_inferencia_ms_muestra"].mean(),
    }

    return resumen, resultados_folds


def _bar_plot(
    df_resumen: pd.DataFrame,
    metrica: str,
    label_y: str,
    titulo: str,
    filename: str,
) -> None:
    modelos = df_resumen["modelo"].tolist()
    medias = df_resumen[metrica + "_mean"].to_numpy()
    desviaciones = df_resumen[metrica + "_std"].to_numpy()

    fig, ax = plt.subplots(figsize=(10, 5))
    barras = ax.bar(modelos, medias, yerr=desviaciones, capsize=5)

    ax.set_ylabel(label_y)
    ax.set_title(titulo)
    ax.set_ylim(0, 1)

    for barra, media in zip(barras, medias):
        ax.text(
            barra.get_x() + barra.get_width() / 2,
            media + 0.015,
            f"{media:.4f}",
            ha="center", va="bottom", fontsize=9,
        )

    plt.xticks(rotation=15)
    plt.tight_layout()
    fig.savefig(CROSS_VALIDATION_DIR / filename, dpi=200, bbox_inches="tight")
    plt.close(fig)


def guardar_graficos(df_resumen: pd.DataFrame) -> None:
    _bar_plot(df_resumen, "accuracy", "Accuracy promedio",
              "Validación cruzada — Accuracy", "cross_validation_accuracy.png")
    _bar_plot(df_resumen, "f1_macro", "F1-macro promedio",
              "Validación cruzada — F1-macro", "cross_validation_f1_macro.png")
    _bar_plot(df_resumen, "mcc", "MCC promedio",
              "Validación cruzada — MCC", "cross_validation_mcc.png")


def main() -> None:
    print("=" * 60)
    print("  VALIDACIÓN CRUZADA — VineGuard AI")
    print("=" * 60)

    print(f"\n  StratifiedKFold con {N_FOLDS} folds")
    print("  Se utiliza únicamente el train original.")
    print("  El conjunto test permanece aislado.")
    print("  No se aplica aumento antes de crear los folds.\n")

    COMPARATIVOS_DIR.mkdir(parents=True, exist_ok=True)
    CROSS_VALIDATION_DIR.mkdir(parents=True, exist_ok=True)

    (X_train, y_train, _, _, _) = load_features(
        fit_scaler=False,
        augment_train=False,
        apply_scaler=False,
    )

    X = np.asarray(X_train, dtype=np.float32)
    y = np.asarray(y_train, dtype=np.int32)

    print(f"  Muestras utilizadas: {len(y)}")
    print(f"  Características: {X.shape[1]}")

    modelos = [
        (
            "M1 — SVM",
            Pipeline([
                ("scaler", StandardScaler()),
                ("modelo", SVC(
                    kernel=M1_SVM_KERNEL,
                    C=M1_SVM_C,
                    gamma=M1_SVM_GAMMA,
                    probability=False,
                    class_weight=M1_SVM_CLASS_WEIGHT,
                    random_state=SEED,
                )),
            ]),
        ),
        (
            "M2 — Random Forest",
            RandomForestClassifier(
                n_estimators=M2_RF_N_ESTIMATORS,
                max_depth=M2_RF_MAX_DEPTH,
                min_samples_split=M2_RF_MIN_SAMPLES_SPLIT,
                min_samples_leaf=M2_RF_MIN_SAMPLES_LEAF,
                class_weight=M2_RF_CLASS_WEIGHT,
                n_jobs=-1,
                random_state=SEED,
            ),
        ),
        (
            "M3 — KNN",
            Pipeline([
                ("scaler", StandardScaler()),
                ("modelo", KNeighborsClassifier(
                    n_neighbors=M3_KNN_N_NEIGHBORS,
                    metric=M3_KNN_METRIC,
                    weights=M3_KNN_WEIGHTS,
                    algorithm=M3_KNN_ALGORITHM,
                    p=M3_KNN_P,
                    n_jobs=-1,
                )),
            ]),
        ),
    ]

    resumenes = []
    todos_los_folds = []

    for nombre, modelo in modelos:
        resumen, resultados_folds = ejecutar_cv(modelo, nombre, X, y)
        resumenes.append(resumen)
        todos_los_folds.extend(resultados_folds)

    df_resumen = pd.DataFrame(resumenes)
    for col in df_resumen.select_dtypes(include=[np.number]).columns:
        df_resumen[col] = df_resumen[col].round(4)

    df_folds = pd.DataFrame(todos_los_folds)
    for col in df_folds.select_dtypes(include=[np.number]).columns:
        df_folds[col] = df_folds[col].round(4)

    df_resumen.to_csv(CROSS_VALIDATION_RESULTADOS_PATH, index=False)
    df_folds.to_csv(CROSS_VALIDATION_DIR / "cross_validation_por_fold.csv", index=False)

    guardar_graficos(df_resumen)

    print("\n" + "=" * 60)
    print("  RESUMEN CROSS-VALIDATION")
    print("=" * 60)
    print(df_resumen.to_string(index=False))

    print(f"\n✅ Resumen guardado en: {CROSS_VALIDATION_RESULTADOS_PATH}")
    print(f"✅ Resultados por fold guardados en: {CROSS_VALIDATION_DIR / 'cross_validation_por_fold.csv'}")
    print(f"✅ Gráfico accuracy:  {CROSS_VALIDATION_DIR / 'cross_validation_accuracy.png'}")
    print(f"✅ Gráfico F1-macro:  {CROSS_VALIDATION_DIR / 'cross_validation_f1_macro.png'}")
    print(f"✅ Gráfico MCC:       {CROSS_VALIDATION_DIR / 'cross_validation_mcc.png'}")
    print(f"\n✅ Validación cruzada completada: M1, M2 y M3")
    print(f"⬜ Validación cruzada pendiente: H1 y H2")


if __name__ == "__main__":
    main()
