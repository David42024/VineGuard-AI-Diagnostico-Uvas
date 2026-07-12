import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.metrics import roc_curve, auc
from sklearn.preprocessing import label_binarize

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mantenedor import (
    TEST_DIR, MODELS_DIR, COMPARATIVOS_DIR,
    IMG_SIZE, SEED, CLASS_NAMES,
    SVM_MODEL_PATH, SVM_SCALER_PATH,
    KNN_MODEL_PATH, KNN_SCALER_PATH,
    CNN_EXTRACTOR_PATH, CNN_SVM_PATH,
    TRANSFER_EXTRACTOR_PATH, TRANSFER_RF_PATH,
)
from extract_features import load_features


def _medir_inferencia(modelo, X, n_warmup=2, n_reps=5):
    tiempos = []
    for _ in range(n_warmup):
        _ = modelo.predict(X)
    for _ in range(n_reps):
        t0 = time.perf_counter()
        _ = modelo.predict(X)
        tiempos.append((time.perf_counter() - t0) / len(X) * 1000)
    return round(np.median(tiempos), 4)


def main():
    COMPARATIVOS_DIR.mkdir(parents=True, exist_ok=True)
    print("=" * 60)
    print("  EVALUACIÓN COMPARATIVA — VineGuard AI")
    print("=" * 60)

    np.random.seed(SEED)
    import tensorflow as tf
    import joblib

    n_classes = len(CLASS_NAMES)
    resultados = []
    roc_data = {}  # model_name -> {fpr, tpr, auc} por clase

    # ── M1 SVM ────────────────────────────────────────────────────────────
    print("\n🔷 M1 - SVM")
    try:
        from extract_features import load_features
        _, _, X_test, y_test = load_features(fit_scaler=False, augment_train=False, apply_scaler=False)
        X_test_scaled = joblib.load(SVM_SCALER_PATH).transform(X_test)
        svm = joblib.load(SVM_MODEL_PATH)
        t_inferencia = _medir_inferencia(svm, X_test_scaled)
        y_score = svm.predict_proba(X_test_scaled)
        y_pred = svm.predict(X_test_scaled)
        acc = (y_pred == y_test).mean()
        roc_data["M1 - SVM"] = {"y_test": y_test, "y_score": y_score}
        resultados.append({"modelo": "M1 - SVM", "accuracy": round(acc, 4), "inferencia_ms": t_inferencia})
        print(f"   Accuracy: {acc:.4f}, Inferencia: {t_inferencia:.2f}ms/muestra")
    except Exception as e:
        print(f"   ⚠️  Error: {e}")

    # ── M2 Random Forest ──────────────────────────────────────────────────
    print("\n🔷 M2 - Random Forest")
    try:
        _, _, X_test, y_test = load_features(fit_scaler=False, augment_train=False, apply_scaler=False)
        rf = joblib.load(RF_MODEL_PATH)
        t_inferencia = _medir_inferencia(rf, X_test)
        y_score = rf.predict_proba(X_test)
        y_pred = rf.predict(X_test)
        acc = (y_pred == y_test).mean()
        roc_data["M2 - Random Forest"] = {"y_test": y_test, "y_score": y_score}
        resultados.append({"modelo": "M2 - Random Forest", "accuracy": round(acc, 4), "inferencia_ms": t_inferencia})
        print(f"   Accuracy: {acc:.4f}, Inferencia: {t_inferencia:.2f}ms/muestra")
    except Exception as e:
        print(f"   ⚠️  Error: {e}")

    # ── M3 KNN ────────────────────────────────────────────────────────────
    print("\n🔷 M3 - KNN")
    try:
        _, _, X_test, y_test = load_features(fit_scaler=False, augment_train=False, apply_scaler=False)
        X_test_scaled = joblib.load(KNN_SCALER_PATH).transform(X_test)
        knn = joblib.load(KNN_MODEL_PATH)
        t_inferencia = _medir_inferencia(knn, X_test_scaled)
        y_score = knn.predict_proba(X_test_scaled)
        y_pred = knn.predict(X_test_scaled)
        acc = (y_pred == y_test).mean()
        roc_data["M3 - KNN"] = {"y_test": y_test, "y_score": y_score}
        resultados.append({"modelo": "M3 - KNN", "accuracy": round(acc, 4), "inferencia_ms": t_inferencia})
        print(f"   Accuracy: {acc:.4f}, Inferencia: {t_inferencia:.2f}ms/muestra")
    except Exception as e:
        print(f"   ⚠️  Error: {e}")

    # ── H1 CNN+SVM ───────────────────────────────────────────────────────
    print("\n🔷 H1 - CNN + SVM")
    try:
        extractor = tf.keras.models.load_model(CNN_EXTRACTOR_PATH)
        svm_cnn = joblib.load(CNN_SVM_PATH)
        X_test_cnn = []
        y_test_h1 = []
        for idx, cls in enumerate(CLASS_NAMES):
            d = TEST_DIR / cls
            for p in sorted(d.iterdir()):
                if p.suffix.lower() in {".jpg", ".jpeg", ".png"}:
                    img = tf.keras.utils.load_img(p, target_size=IMG_SIZE)
                    arr = tf.keras.utils.img_to_array(img) / 255.0
                    X_test_cnn.append(arr)
                    y_test_h1.append(idx)
        X_test_cnn = np.array(X_test_cnn)
        y_test_h1 = np.array(y_test_h1)

        t0 = time.perf_counter()
        feats = extractor.predict(X_test_cnn, verbose=0)
        t_inferencia = round((time.perf_counter() - t0) / len(y_test_h1) * 1000, 4)
        y_score = svm_cnn.predict_proba(feats)
        y_pred = svm_cnn.predict(feats)
        acc = (y_pred == y_test_h1).mean()
        roc_data["H1 - CNN + SVM"] = {"y_test": y_test_h1, "y_score": y_score}
        resultados.append({"modelo": "H1 - CNN + SVM", "accuracy": round(acc, 4), "inferencia_ms": t_inferencia})
        print(f"   Accuracy: {acc:.4f}, Inferencia: {t_inferencia:.2f}ms/muestra")
    except Exception as e:
        print(f"   ⚠️  Error: {e}")

    # ── H2 MobileNetV2+RF ────────────────────────────────────────────────
    print("\n🔷 H2 - MobileNetV2 + RF")
    try:
        from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
        extractor_t = tf.keras.models.load_model(TRANSFER_EXTRACTOR_PATH)
        rf_t = joblib.load(TRANSFER_RF_PATH)
        X_test_t = []
        y_test_h2 = []
        for idx, cls in enumerate(CLASS_NAMES):
            d = TEST_DIR / cls
            for p in sorted(d.iterdir()):
                if p.suffix.lower() in {".jpg", ".jpeg", ".png"}:
                    img = tf.keras.utils.load_img(p, target_size=IMG_SIZE)
                    arr = tf.keras.utils.img_to_array(img)
                    arr = preprocess_input(arr)
                    X_test_t.append(arr)
                    y_test_h2.append(idx)
        X_test_t = np.array(X_test_t)
        y_test_h2 = np.array(y_test_h2)

        t0 = time.perf_counter()
        feats_t = extractor_t.predict(X_test_t, verbose=0)
        t_inferencia = round((time.perf_counter() - t0) / len(y_test_h2) * 1000, 4)
        y_score = rf_t.predict_proba(feats_t)
        y_pred = rf_t.predict(feats_t)
        acc = (y_pred == y_test_h2).mean()
        roc_data["H2 - MobileNetV2 + RF"] = {"y_test": y_test_h2, "y_score": y_score}
        resultados.append({"modelo": "H2 - MobileNetV2 + RF", "accuracy": round(acc, 4), "inferencia_ms": t_inferencia})
        print(f"   Accuracy: {acc:.4f}, Inferencia: {t_inferencia:.2f}ms/muestra")
    except Exception as e:
        print(f"   ⚠️  Error: {e}")

    # ── Guardar benchmark ────────────────────────────────────────────────
    if resultados:
        bench_df = pd.DataFrame(resultados)
        bench_path = COMPARATIVOS_DIR / "benchmark_inferencia.csv"
        bench_df.to_csv(bench_path, index=False)
        print(f"\n✅ Benchmark guardado: {bench_path}")
        print(bench_df.to_string(index=False))

    # ── ROC superpuestas ─────────────────────────────────────────────────
    if len(roc_data) < 2:
        print("\n⚠️  No hay suficientes modelos para graficar ROC.")
        return

    fig, ax = plt.subplots(figsize=(9, 8))
    colors = ["#e74c3c", "#3498db", "#2ecc71", "#f39c12", "#9b59b6"]
    linestyles = ["-", "--", "-.", ":", (0, (3, 1, 1, 1))]

    for idx, (model_name, data) in enumerate(roc_data.items()):
        y_t = data["y_test"]
        y_s = data["y_score"]
        y_b = label_binarize(y_t, classes=range(n_classes))

        for i in range(n_classes):
            fpr_i, tpr_i, _ = roc_curve(y_b[:, i], y_s[:, i])
            auc_i = auc(fpr_i, tpr_i)

        fpr_micro, tpr_micro, _ = roc_curve(y_b.ravel(), y_s.ravel())
        auc_micro = auc(fpr_micro, tpr_micro)

        color = colors[idx % len(colors)]
        ls = linestyles[idx % len(linestyles)]
        ax.plot(fpr_micro, tpr_micro, color=color, ls=ls, lw=2,
                label=f"{model_name} (micro-AUC={auc_micro:.3f})")

    ax.plot([0, 1], [0, 1], "gray", lw=1, linestyle=":")
    ax.set(xlim=[-0.02, 1.02], ylim=[-0.02, 1.05],
           xlabel="Tasa de Falsos Positivos (1 - Especificidad)",
           ylabel="Tasa de Verdaderos Positivos (Sensibilidad)")
    ax.set_title("Comparación de Curvas ROC — Todos los Modelos (Micro-promedio)", fontsize=13, fontweight="bold")
    ax.legend(loc="lower right", fontsize=9)
    ax.grid(alpha=0.3)
    fig.tight_layout()

    roc_path = COMPARATIVOS_DIR / "comparacion_roc_modelos.png"
    fig.savefig(roc_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"\n✅ ROC superpuestas guardadas: {roc_path}")

    print("\n✅ Evaluación comparativa completada.")


if __name__ == "__main__":
    main()
