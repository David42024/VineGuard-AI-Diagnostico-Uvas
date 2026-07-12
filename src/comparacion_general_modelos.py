import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mantenedor import CLASS_NAMES, COMPARATIVOS_DIR, M1_SVM_REPORTS_DIR, M2_RF_REPORTS_DIR, M3_KNN_REPORTS_DIR, H1_CNN_SVM_REPORTS_DIR, H2_TRANSFER_RF_REPORTS_DIR

RESULTADOS_FILES = [
    ("M1 - SVM", M1_SVM_REPORTS_DIR, "resultados_m1_svm.csv"),
    ("M2 - Random Forest", M2_RF_REPORTS_DIR, "resultados_m2_random_forest.csv"),
    ("M3 - KNN", M3_KNN_REPORTS_DIR, "resultados_m3_knn.csv"),
    ("H1 - CNN + SVM", H1_CNN_SVM_REPORTS_DIR, "resultados_h1_cnn_svm.csv"),
    ("H2 - MobileNetV2 + RF", H2_TRANSFER_RF_REPORTS_DIR, "resultados_h2_transfer_rf.csv"),
]

REPORTE_FILES = [
    ("M1 - SVM", M1_SVM_REPORTS_DIR, "reporte_clasificacion_m1_svm.csv"),
    ("M2 - Random Forest", M2_RF_REPORTS_DIR, "reporte_clasificacion_m2_random_forest.csv"),
    ("M3 - KNN", M3_KNN_REPORTS_DIR, "reporte_clasificacion_m3_knn.csv"),
    ("H1 - CNN + SVM", H1_CNN_SVM_REPORTS_DIR, "reporte_clasificacion_h1_cnn_svm.csv"),
    ("H2 - MobileNetV2 + RF", H2_TRANSFER_RF_REPORTS_DIR, "reporte_clasificacion_h2_transfer_rf.csv"),
]

COLUMNS_ORDER = [
    "modelo", "accuracy", "balanced_accuracy", "precision", "recall",
    "f1_score", "mcc", "auc_macro", "auc_micro",
    "tiempo_carga_preprocesamiento_features_s", "tiempo_entrenamiento_s",
    "tiempo_evaluacion_s", "tiempo_total_proceso_s", "tiempo_inferencia_ms",
]


def main():
    COMPARATIVOS_DIR.mkdir(parents=True, exist_ok=True)

    # ── Tabla general ──────────────────────────────────────────────────────
    rows = []
    for nombre, base_dir, filename in RESULTADOS_FILES:
        path = base_dir / filename
        if not path.exists():
            print(f"  ⚠️  No encontrado: {path}")
            continue
        df = pd.read_csv(path)
        rows.append(df)

    if not rows:
        print("No se encontraron resultados de entrenamiento. Ejecuta primero los scripts de entrenamiento.")
        return

    comparativa = pd.concat(rows, ignore_index=True)

    cols_presentes = [c for c in COLUMNS_ORDER if c in comparativa.columns]
    comparativa = comparativa[cols_presentes]

    comparativa = comparativa.sort_values("f1_score", ascending=False).reset_index(drop=True)
    comparativa.insert(0, "ranking", range(1, len(comparativa) + 1))

    ruta_salida = COMPARATIVOS_DIR / "comparacion_general_modelos.csv"
    comparativa.to_csv(ruta_salida, index=False)
    print(f"\n✅ Tabla comparativa guardada: {ruta_salida}")
    print(f"   Modelos: {len(comparativa)}")
    print(f"   Columnas: {', '.join(cols_presentes)}")
    print(f"   Ranking por F1-score\n")
    print(comparativa.to_string(index=False))

    # ── Tabla F1 por clase ────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  F1-Score POR CLASE — Comparativa entre modelos")
    print("=" * 60)

    f1_rows = []
    for nombre, base_dir, filename in REPORTE_FILES:
        path = base_dir / filename
        if not path.exists():
            continue
        reporte = pd.read_csv(path, index_col=0)
        fila = {"modelo": nombre}
        for cls in CLASS_NAMES:
            if cls in reporte.index and "f1-score" in reporte.columns:
                fila[cls] = round(reporte.loc[cls, "f1-score"], 4)
            else:
                fila[cls] = None
        f1_rows.append(fila)

    if f1_rows:
        f1_df = pd.DataFrame(f1_rows)
        f1_cols = ["modelo"] + CLASS_NAMES
        f1_df = f1_df[f1_cols]
        f1_df = f1_df.sort_values(CLASS_NAMES[0], ascending=False).reset_index(drop=True)

        ruta_f1 = COMPARATIVOS_DIR / "comparacion_f1_por_clase.csv"
        f1_df.to_csv(ruta_f1, index=False)
        print(f"\n  ✅ Guardado: {ruta_f1}\n")
        print(f1_df.to_string(index=False))


if __name__ == "__main__":
    main()
