"""
train_m1_svm.py
───────────────
M1 — Support Vector Machine (SVM)

Flujo:
  1. Cargar, preprocesar y extraer características.
  2. Balancear train mediante aumento dinámico.
  3. Estandarizar las características.
  4. Entrenar SVM con kernel RBF.
  5. Evaluar sobre test sin aumento.
  6. Generar reportes y guardar el modelo.
"""

import sys
import time
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
elif hasattr(sys.stdout, "buffer"):
    import io

    sys.stdout = io.TextIOWrapper(
        sys.stdout.buffer,
        encoding="utf-8",
    )

import joblib
import pandas as pd

from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    matthews_corrcoef,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.preprocessing import label_binarize
from sklearn.svm import SVC

sys.path.insert(
    0,
    str(Path(__file__).resolve().parent),
)

from mantenedor import (
    CLASS_NAMES,
    M1_SVM_REPORTS_DIR,
    SVM_MODEL_PATH,
    SVM_SCALER_PATH,
)
from extract_features import load_features
from evaluacion_visual import (
    save_confusion_matrix,
    save_normalized_confusion_matrix,
    save_precision_recall_curves,
    save_roc_curves,
)


SEMILLA = 42
NOMBRE_MODELO = "M1 — SVM (RBF)"


def calcular_metricas(
    y_test,
    y_pred,
    y_score,
) -> dict:
    """
    Calcula métricas generales, AUC y matriz de confusión.
    """
    metricas = {
        "accuracy": accuracy_score(y_test, y_pred),
        "balanced_accuracy": balanced_accuracy_score(
            y_test,
            y_pred,
        ),
        "precision": precision_score(
            y_test,
            y_pred,
            average="weighted",
            zero_division=0,
        ),
        "recall": recall_score(
            y_test,
            y_pred,
            average="weighted",
            zero_division=0,
        ),
        "f1_score": f1_score(
            y_test,
            y_pred,
            average="weighted",
            zero_division=0,
        ),
        "mcc": matthews_corrcoef(
            y_test,
            y_pred,
        ),
        "confusion_matrix": confusion_matrix(
            y_test,
            y_pred,
        ),
    }

    y_bin = label_binarize(
        y_test,
        classes=range(len(CLASS_NAMES)),
    )

    try:
        metricas["auc_macro"] = roc_auc_score(
            y_bin,
            y_score,
            multi_class="ovr",
            average="macro",
        )
        metricas["auc_micro"] = roc_auc_score(
            y_bin,
            y_score,
            multi_class="ovr",
            average="micro",
        )
    except ValueError:
        metricas["auc_macro"] = 0.0
        metricas["auc_micro"] = 0.0

    return metricas


def mostrar_resultados(
    y_test,
    y_pred,
    metricas: dict,
    tiempo_carga_s: float,
    tiempo_entrenamiento_s: float,
    tiempo_inferencia_ms: float,
) -> None:
    """
    Muestra métricas y matriz de confusión en consola.
    """
    cm = metricas["confusion_matrix"]

    print("\n" + "=" * 60)
    print(f"  📊 RESULTADOS — {NOMBRE_MODELO}")
    print("=" * 60)
    print(
        f"   Accuracy          : "
        f"{metricas['accuracy']:.4f} "
        f"({metricas['accuracy']:.2%})"
    )
    print(
        f"   Balanced Accuracy : "
        f"{metricas['balanced_accuracy']:.4f}"
    )
    print(
        f"   Precision         : "
        f"{metricas['precision']:.4f}"
    )
    print(
        f"   Recall            : "
        f"{metricas['recall']:.4f}"
    )
    print(
        f"   F1-Score          : "
        f"{metricas['f1_score']:.4f}"
    )
    print(
        f"   MCC               : "
        f"{metricas['mcc']:.4f}"
    )
    print(
        f"   AUC Macro         : "
        f"{metricas['auc_macro']:.4f}"
    )
    print(
        f"   AUC Micro         : "
        f"{metricas['auc_micro']:.4f}"
    )
    print(
        "   Tiempo carga/preprocesamiento/features: "
        f"{tiempo_carga_s:.2f}s"
    )
    print(
        "   Tiempo entrenamiento                  : "
        f"{tiempo_entrenamiento_s:.2f}s"
    )
    print(
        "   Inferencia promedio por muestra       : "
        f"{tiempo_inferencia_ms:.4f}ms"
    )

    print("\n   Reporte por clase:")
    print(
        classification_report(
            y_test,
            y_pred,
            target_names=CLASS_NAMES,
            zero_division=0,
        )
    )

    print("   Matriz de Confusión:")

    header = "         " + "  ".join(
        f"{clase[:8]:>8}"
        for clase in CLASS_NAMES
    )
    print(header)

    for index, fila in enumerate(cm):
        valores = "  ".join(
            f"{valor:>8}"
            for valor in fila
        )
        print(
            f"  {CLASS_NAMES[index][:8]:>8}  "
            f"{valores}"
        )

    print("=" * 60)


def guardar_reportes_evaluacion(
    y_test,
    y_pred,
    y_score,
    filenames_test,
    metricas: dict,
) -> None:
    """
    Guarda reportes de clasificación, matrices, curvas
    y predicciones individuales.
    """
    M1_SVM_REPORTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    reporte = classification_report(
        y_test,
        y_pred,
        target_names=CLASS_NAMES,
        zero_division=0,
        output_dict=True,
    )

    pd.DataFrame(reporte).transpose().to_csv(
        M1_SVM_REPORTS_DIR
        / "reporte_clasificacion_m1_svm.csv"
    )

    pd.DataFrame(
        metricas["confusion_matrix"],
        index=CLASS_NAMES,
        columns=CLASS_NAMES,
    ).to_csv(
        M1_SVM_REPORTS_DIR
        / "confusion_m1_svm.csv"
    )

    save_confusion_matrix(
        y_test,
        y_pred,
        CLASS_NAMES,
        M1_SVM_REPORTS_DIR
        / "confusion_m1_svm.png",
    )

    save_normalized_confusion_matrix(
        y_test,
        y_pred,
        CLASS_NAMES,
        M1_SVM_REPORTS_DIR
        / "confusion_normalizada_m1_svm.png",
    )

    save_roc_curves(
        y_test,
        y_score,
        CLASS_NAMES,
        M1_SVM_REPORTS_DIR
        / "roc_m1_svm.png",
    )

    save_precision_recall_curves(
        y_test,
        y_score,
        CLASS_NAMES,
        M1_SVM_REPORTS_DIR
        / "precision_recall_m1_svm.png",
    )

    predicciones = pd.DataFrame({
        "archivo": filenames_test,
        "clase_real": [
            CLASS_NAMES[int(etiqueta)]
            for etiqueta in y_test
        ],
        "clase_predicha": [
            CLASS_NAMES[int(etiqueta)]
            for etiqueta in y_pred
        ],
        "prob_Black_rot": y_score[:, 0],
        "prob_Esca": y_score[:, 1],
        "prob_Healthy": y_score[:, 2],
        "prob_Leaf_blight": y_score[:, 3],
        "correcto": y_test == y_pred,
    })

    predicciones.to_csv(
        M1_SVM_REPORTS_DIR
        / "predicciones_m1_svm.csv",
        index=False,
    )


def guardar_resumen_final(
    metricas: dict,
    tiempo_carga_s: float,
    tiempo_entrenamiento_s: float,
    tiempo_evaluacion_s: float,
    tiempo_inferencia_ms: float,
    tiempo_guardado_modelo_s: float,
    tiempo_total_s: float,
    n_muestras_train: int,
    n_muestras_test: int,
    n_features: int,
    model_size_mb: float,
) -> None:
    """
    Guarda el CSV general con todas las métricas y tiempos definitivos.
    """
    resumen = {
        "modelo": NOMBRE_MODELO,
        "accuracy": round(
            metricas["accuracy"],
            4,
        ),
        "balanced_accuracy": round(
            metricas["balanced_accuracy"],
            4,
        ),
        "precision": round(
            metricas["precision"],
            4,
        ),
        "recall": round(
            metricas["recall"],
            4,
        ),
        "f1_score": round(
            metricas["f1_score"],
            4,
        ),
        "mcc": round(
            metricas["mcc"],
            4,
        ),
        "auc_macro": round(
            metricas["auc_macro"],
            4,
        ),
        "auc_micro": round(
            metricas["auc_micro"],
            4,
        ),
        "tiempo_carga_preprocesamiento_features_s": round(
            tiempo_carga_s,
            2,
        ),
        "tiempo_entrenamiento_s": round(
            tiempo_entrenamiento_s,
            2,
        ),
        "tiempo_evaluacion_s": round(
            tiempo_evaluacion_s,
            2,
        ),
        "tiempo_inferencia_ms": round(
            tiempo_inferencia_ms,
            4,
        ),
        "tiempo_guardado_modelo_s": round(
            tiempo_guardado_modelo_s,
            4,
        ),
        "tiempo_total_proceso_s": round(
            tiempo_total_s,
            2,
        ),
        "n_muestras_train": n_muestras_train,
        "n_muestras_test": n_muestras_test,
        "n_features": n_features,
        "model_size_mb": round(
            model_size_mb,
            3,
        ),
        "semilla": SEMILLA,
        "kernel": "rbf",
        "C": 10.0,
        "gamma": "scale",
        "class_weight": "balanced",
    }

    pd.DataFrame([resumen]).to_csv(
        M1_SVM_REPORTS_DIR
        / "resultados_m1_svm.csv",
        index=False,
    )


def mostrar_resumen_tiempos(
    tiempo_carga_s: float,
    tiempo_entrenamiento_s: float,
    tiempo_evaluacion_s: float,
    tiempo_inferencia_ms: float,
    tiempo_guardado_modelo_s: float,
    tiempo_total_s: float,
) -> None:
    """
    Muestra el resumen final de tiempos.
    """
    print("\n" + "=" * 60)
    print("  RESUMEN DE TIEMPOS")
    print("=" * 60)
    print(
        "  Carga, preprocesamiento y features : "
        f"{tiempo_carga_s:.2f} s"
    )
    print(
        "  Entrenamiento                      : "
        f"{tiempo_entrenamiento_s:.2f} s"
    )
    print(
        "  Evaluación completa y reportes     : "
        f"{tiempo_evaluacion_s:.2f} s"
    )
    print(
        "  Inferencia promedio por muestra    : "
        f"{tiempo_inferencia_ms:.4f} ms"
    )
    print(
        "  Guardado del modelo                : "
        f"{tiempo_guardado_modelo_s:.4f} s"
    )
    print(
        "  Tiempo total del proceso           : "
        f"{tiempo_total_s:.2f} s"
    )
    print("=" * 60)


def main() -> None:
    print("=" * 60)
    print("  M1 — Entrenamiento SVM — VineGuard AI")
    print("=" * 60)

    M1_SVM_REPORTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )
    SVM_MODEL_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    inicio_total = time.perf_counter()

    # ─────────────────────────────────────────────
    # 1. Carga, preprocesamiento y características
    # ─────────────────────────────────────────────
    inicio_carga = time.perf_counter()

    (
        X_train,
        y_train,
        X_test,
        y_test,
        filenames_test,
    ) = load_features(
        fit_scaler=True,
        augment_train=True,
        apply_scaler=True,
        scaler_path=SVM_SCALER_PATH,
    )

    tiempo_carga = (
        time.perf_counter() - inicio_carga
    )

    print(
        "   ✅ Carga y preprocesamiento completados "
        f"en {tiempo_carga:.2f}s"
    )

    print(
        "\n📦 Datos cargados: "
        f"Train: {X_train.shape[0]} muestras, "
        f"Test: {X_test.shape[0]} muestras, "
        f"Features: {X_train.shape[1]}"
    )

    if len(X_train) == 0:
        raise ValueError(
            "El conjunto de entrenamiento está vacío."
        )

    if len(X_test) == 0:
        raise ValueError(
            "El conjunto de test está vacío."
        )

    # ─────────────────────────────────────────────
    # 2. Entrenamiento
    # ─────────────────────────────────────────────
    modelo = SVC(
        kernel="rbf",
        C=10.0,
        gamma="scale",
        probability=True,
        class_weight="balanced",
        random_state=SEMILLA,
        verbose=False,
    )

    inicio_entrenamiento = time.perf_counter()

    modelo.fit(
        X_train,
        y_train,
    )

    tiempo_entrenamiento = (
        time.perf_counter()
        - inicio_entrenamiento
    )

    print(
        "   ✅ Entrenamiento completado "
        f"en {tiempo_entrenamiento:.2f}s"
    )

    # ─────────────────────────────────────────────
    # 3. Evaluación completa
    # Incluye inferencia, métricas, CSV y gráficos
    # ─────────────────────────────────────────────
    inicio_evaluacion = time.perf_counter()

    inicio_inferencia = time.perf_counter()

    y_pred = modelo.predict(X_test)
    y_score = modelo.predict_proba(X_test)

    duracion_inferencia = (
        time.perf_counter()
        - inicio_inferencia
    )

    tiempo_inferencia_ms = (
        duracion_inferencia
        / len(y_pred)
    ) * 1000

    metricas = calcular_metricas(
        y_test,
        y_pred,
        y_score,
    )

    mostrar_resultados(
        y_test,
        y_pred,
        metricas,
        tiempo_carga,
        tiempo_entrenamiento,
        tiempo_inferencia_ms,
    )

    guardar_reportes_evaluacion(
        y_test,
        y_pred,
        y_score,
        filenames_test,
        metricas,
    )

    tiempo_evaluacion = (
        time.perf_counter()
        - inicio_evaluacion
    )

    # ─────────────────────────────────────────────
    # 4. Guardado definitivo del modelo
    # ─────────────────────────────────────────────
    inicio_guardado_modelo = time.perf_counter()

    joblib.dump(
        modelo,
        SVM_MODEL_PATH,
    )

    tiempo_guardado_modelo = (
        time.perf_counter()
        - inicio_guardado_modelo
    )

    model_size_mb = (
        SVM_MODEL_PATH.stat().st_size
        / (1024 * 1024)
    )

    # El total incluye carga, entrenamiento,
    # evaluación, reportes y guardado del modelo.
    tiempo_total = (
        time.perf_counter()
        - inicio_total
    )

    guardar_resumen_final(
        metricas=metricas,
        tiempo_carga_s=tiempo_carga,
        tiempo_entrenamiento_s=tiempo_entrenamiento,
        tiempo_evaluacion_s=tiempo_evaluacion,
        tiempo_inferencia_ms=tiempo_inferencia_ms,
        tiempo_guardado_modelo_s=tiempo_guardado_modelo,
        tiempo_total_s=tiempo_total,
        n_muestras_train=X_train.shape[0],
        n_muestras_test=X_test.shape[0],
        n_features=X_train.shape[1],
        model_size_mb=model_size_mb,
    )

    mostrar_resumen_tiempos(
        tiempo_carga_s=tiempo_carga,
        tiempo_entrenamiento_s=tiempo_entrenamiento,
        tiempo_evaluacion_s=tiempo_evaluacion,
        tiempo_inferencia_ms=tiempo_inferencia_ms,
        tiempo_guardado_modelo_s=tiempo_guardado_modelo,
        tiempo_total_s=tiempo_total,
    )

    print(
        f"\n💾 Modelo guardado en: "
        f"{SVM_MODEL_PATH}"
    )
    print(
        f"📁 Reportes guardados en: "
        f"{M1_SVM_REPORTS_DIR}"
    )
    print("\n✅ Proceso completado.")


if __name__ == "__main__":
    main()