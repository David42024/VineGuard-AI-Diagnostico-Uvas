import sys
import time
from pathlib import Path
import numpy as np

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
elif hasattr(sys.stdout, 'buffer'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import pandas as pd
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report, matthews_corrcoef, balanced_accuracy_score,
)

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mantenedor import CLASS_NAMES, RF_MODEL_PATH, MODELS_DIR, MODELOS_DIR
from extract_features import load_features
from evaluacion_visual import save_confusion_matrix, save_roc_curves


def mostrar_metricas(y_test, y_pred, nombre_modelo="Random Forest", tiempo_entrenamiento=0, tiempo_inferencia=0):
    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred, average="weighted", zero_division=0)
    rec = recall_score(y_test, y_pred, average="weighted", zero_division=0)
    f1 = f1_score(y_test, y_pred, average="weighted", zero_division=0)
    mcc = matthews_corrcoef(y_test, y_pred)
    cm = confusion_matrix(y_test, y_pred)
    bal_acc = balanced_accuracy_score(y_test, y_pred)

    print("\n" + "=" * 60)
    print(f"  📊 RESULTADOS — {nombre_modelo}")
    print("=" * 60)
    print(f"  Accuracy          : {acc:.4f}  ({acc:.2%})")
    print(f"  Balanced Accuracy : {bal_acc:.4f}")
    print(f"  Precision         : {prec:.4f}")
    print(f"  Recall            : {rec:.4f}")
    print(f"  F1-Score          : {f1:.4f}")
    print(f"  MCC               : {mcc:.4f}")
    print(f"  Tiempo entrenamiento: {tiempo_entrenamiento:.2f}s")
    print(f"  Tiempo inferencia   : {tiempo_inferencia:.2f}ms")
    print("\n  Reporte por clase:")
    print(classification_report(y_test, y_pred, target_names=CLASS_NAMES, zero_division=0))
    print("  Matriz de Confusión:")
    header = "         " + "  ".join(f"{c[:8]:>8}" for c in CLASS_NAMES)
    print(header)
    for i, row in enumerate(cm):
        row_str = "  ".join(f"{v:>8}" for v in row)
        print(f"  {CLASS_NAMES[i][:8]:>8}  {row_str}")
    print("=" * 60)

    MODELOS_DIR.mkdir(parents=True, exist_ok=True)
    reporte = classification_report(y_test, y_pred, target_names=CLASS_NAMES, zero_division=0, output_dict=True)
    reporte_df = pd.DataFrame(reporte).transpose()
    ruta_reporte = MODELOS_DIR / "reporte_clasificacion_m2_random_forest.csv"
    reporte_df.to_csv(ruta_reporte)
    print(f"  Reporte por clase guardado: {ruta_reporte}")

    cm_df = pd.DataFrame(cm, index=CLASS_NAMES, columns=CLASS_NAMES)
    cm_df.to_csv(MODELOS_DIR / "confusion_m2_random_forest.csv")

    resumen = pd.DataFrame([{
        "modelo": nombre_modelo, "accuracy": round(acc, 4), "balanced_accuracy": round(bal_acc, 4),
        "precision": round(prec, 4), "recall": round(rec, 4), "f1_score": round(f1, 4),
        "mcc": round(mcc, 4), "tiempo_entrenamiento_s": round(tiempo_entrenamiento, 2),
        "tiempo_inferencia_ms": round(tiempo_inferencia, 2)
    }])
    ruta_resumen = MODELOS_DIR / "resultados_m2_random_forest.csv"
    resumen.to_csv(ruta_resumen, index=False)
    print(f"  Métricas generales guardadas: {ruta_resumen}")
    return acc, prec, rec, f1, mcc, bal_acc, cm


def main():
    print("=" * 60)
    print("  M2 — Entrenamiento Random Forest — VineGuard AI")
    print("=" * 60)

    print("\n🔄 Cargando características con aumento de datos...")
    X_train, y_train, X_test, y_test = load_features(fit_scaler=False, augment_train=True, apply_scaler=False)
    print("   ✅ Test sin aumento — solo preprocesamiento básico")
    print(f"\n📦 Datos cargados: Train: {X_train.shape[0]} muestras, Test: {X_test.shape[0]} muestras")

    print("\n🚀 Entrenando Random Forest (n_estimators=200)...")
    start_train = time.time()
    model = RandomForestClassifier(
        n_estimators=200, max_depth=None, min_samples_split=2,
        min_samples_leaf=1, class_weight=None, n_jobs=-1, random_state=42,
    )
    model.fit(X_train, y_train)
    tiempo_entrenamiento = time.time() - start_train
    print("   ✅ Entrenamiento completado.")

    if len(X_test) == 0:
        raise ValueError("El conjunto de test está vacío.")

    start_infer = time.time()
    y_pred = model.predict(X_test)
    y_score = model.predict_proba(X_test)
    tiempo_inferencia = (time.time() - start_infer) / len(y_pred) * 1000

    importancias = model.feature_importances_
    top_idx = np.argsort(importancias)[::-1][:10]
    print("\n   Top 10 características más importantes:")
    for posicion, idx in enumerate(top_idx, start=1):
        print(f"   {posicion:>2}. Feature {idx:<3}  importancia: {importancias[idx]:.6f}")

    mostrar_metricas(y_test, y_pred, "M2 — Random Forest", tiempo_entrenamiento, tiempo_inferencia)

    MODELOS_DIR.mkdir(parents=True, exist_ok=True)
    save_confusion_matrix(y_test, y_pred, CLASS_NAMES, MODELOS_DIR / "confusion_m2_random_forest.png")
    save_roc_curves(y_test, y_score, CLASS_NAMES, MODELOS_DIR / "roc_m2_random_forest.png")

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, RF_MODEL_PATH)
    print(f"\n💾 Modelo guardado en: {RF_MODEL_PATH}")
    print("\n✅ Proceso completado.")


if __name__ == "__main__":
    main()
