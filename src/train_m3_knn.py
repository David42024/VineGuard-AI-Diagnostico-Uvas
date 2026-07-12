import sys
import time
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
elif hasattr(sys.stdout, 'buffer'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import pandas as pd
import joblib
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report, matthews_corrcoef, balanced_accuracy_score,
)

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mantenedor import CLASS_NAMES, KNN_MODEL_PATH, KNN_SCALER_PATH, MODELS_DIR, MODELOS_DIR
from extract_features import load_features
from evaluacion_visual import save_confusion_matrix, save_roc_curves


def mostrar_metricas(y_test, y_pred, nombre_modelo="KNN", tiempo_entrenamiento=0, tiempo_inferencia=0):
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
    ruta_reporte = MODELOS_DIR / "reporte_clasificacion_m3_knn.csv"
    reporte_df.to_csv(ruta_reporte)
    print(f"  Reporte por clase guardado: {ruta_reporte}")

    cm_df = pd.DataFrame(cm, index=CLASS_NAMES, columns=CLASS_NAMES)
    cm_df.to_csv(MODELOS_DIR / "confusion_m3_knn.csv")

    resumen = pd.DataFrame([{
        "modelo": nombre_modelo, "accuracy": round(acc, 4), "balanced_accuracy": round(bal_acc, 4),
        "precision": round(prec, 4), "recall": round(rec, 4), "f1_score": round(f1, 4),
        "mcc": round(mcc, 4), "tiempo_entrenamiento_s": round(tiempo_entrenamiento, 2),
        "tiempo_inferencia_ms": round(tiempo_inferencia, 2)
    }])
    ruta_resumen = MODELOS_DIR / "resultados_m3_knn.csv"
    resumen.to_csv(ruta_resumen, index=False)
    print(f"  Métricas generales guardadas: {ruta_resumen}")
    return acc, prec, rec, f1, mcc, bal_acc, cm


def main():
    print("=" * 60)
    print("  M3 — Entrenamiento KNN — VineGuard AI")
    print("=" * 60)

    print("\n🔄 Cargando características con aumento de datos...")
    X_train, y_train, X_test, y_test = load_features(fit_scaler=True, augment_train=True, apply_scaler=True, scaler_path=KNN_SCALER_PATH)
    print("   ✅ Test sin aumento — solo preprocesamiento básico")
    print(f"\n📦 Datos cargados: Train: {X_train.shape[0]} muestras, Test: {X_test.shape[0]} muestras")

    print("\n🚀 Entrenando KNN (k=5, métrica=euclidiana)...")
    start_train = time.time()
    model = KNeighborsClassifier(
        n_neighbors=5, metric="euclidean", weights="distance", algorithm="auto", n_jobs=-1,
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

    mostrar_metricas(y_test, y_pred, "M3 — KNN (k=5, euclidiana)", tiempo_entrenamiento, tiempo_inferencia)

    MODELOS_DIR.mkdir(parents=True, exist_ok=True)
    save_confusion_matrix(y_test, y_pred, CLASS_NAMES, MODELOS_DIR / "confusion_m3_knn.png")
    save_roc_curves(y_test, y_score, CLASS_NAMES, MODELOS_DIR / "roc_m3_knn.png")

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, KNN_MODEL_PATH)
    print(f"\n💾 Modelo guardado en: {KNN_MODEL_PATH}")
    print("\n✅ Proceso completado.")


if __name__ == "__main__":
    main()
