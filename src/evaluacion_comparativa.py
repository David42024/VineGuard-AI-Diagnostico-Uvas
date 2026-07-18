import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    matthews_corrcoef,
    roc_curve,
    auc,
)
from sklearn.preprocessing import label_binarize

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mantenedor import (
    TEST_DIR,
    COMPARATIVOS_DIR,
    IMG_SIZE,
    SEED,
    CLASS_NAMES,
    M1_SVM_TUNING_PATH,
    M2_RF_TUNING_PATH,
    M3_KNN_TUNING_PATH,
    H2_RF_TUNING_PATH,
    H2_EXTRACTOR_TUNING_PATH,
    CNN_EXTRACTOR_PATH,
    CNN_SVM_PATH,
)
from extract_features import extract_single_image_features
from validacion_estadistica_modelos import obtener_archivos_test, extraer_embeddings_desde_archivos


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
    import joblib
    import tensorflow as tf
    from tensorflow.keras.preprocessing.image import img_to_array
    from PIL import Image

    COMPARATIVOS_DIR.mkdir(parents=True, exist_ok=True)
    np.random.seed(SEED)
    n_classes = len(CLASS_NAMES)

    print("=" * 60)
    print("  EVALUACIÓN COMPARATIVA — VineGuard AI")
    print("  Ranking por MCC, F1-macro y Accuracy")
    print("=" * 60)

    archivos_test, y_true = obtener_archivos_test()
    n_test = len(y_true)
    print(f"\n📊 Total imágenes TEST: {n_test}")

    # ── Características clásicas (una sola vez para M1/M2/M3) ────────
    print("🔄 Extrayendo características clásicas...")
    X_test_clasicas = np.vstack([
        np.asarray(
            extract_single_image_features(p, apply_scaler=False),
            dtype=np.float32,
        ).reshape(1, -1)
        for p in archivos_test
    ])
    print(f"  Características clásicas TEST: {X_test_clasicas.shape}")

    # ── Evaluar cada modelo y guardar predicciones ──────────────────
    modelos_eval = []

    def evaluar(nombre, cargar_fn, X, medir_inferencia=True):
        nonlocal modelos_eval
        try:
            modelo = cargar_fn()
            y_prob = modelo.predict_proba(X)
            y_pred = modelo.predict(X)
            t_inf = _medir_inferencia(modelo, X) if medir_inferencia else None
            acc = accuracy_score(y_true, y_pred)
            ba = balanced_accuracy_score(y_true, y_pred)
            prec = precision_score(y_true, y_pred, average="macro", zero_division=0)
            rec = recall_score(y_true, y_pred, average="macro", zero_division=0)
            f1 = f1_score(y_true, y_pred, average="macro", zero_division=0)
            mcc = matthews_corrcoef(y_true, y_pred)
            modelos_eval.append({
                "nombre": nombre,
                "y_pred": y_pred,
                "y_prob": y_prob,
                "accuracy": round(acc, 4),
                "balanced_accuracy": round(ba, 4),
                "precision": round(prec, 4),
                "recall": round(rec, 4),
                "f1_score": round(f1, 4),
                "f1_score_raw": f1,
                "mcc": round(mcc, 4),
                "tiempo_inferencia_ms": t_inf,
            })
            print(f"  ✅ {nombre} | Acc: {acc:.4f} | MCC: {mcc:.4f}")
        except Exception as e:
            print(f"  ⚠️  {nombre}: {e}")

    # M1
    evaluar("M1 - SVM", lambda: joblib.load(M1_SVM_TUNING_PATH), X_test_clasicas)
    # M2
    evaluar("M2 - Random Forest", lambda: joblib.load(M2_RF_TUNING_PATH), X_test_clasicas)
    # M3
    evaluar("M3 - KNN", lambda: joblib.load(M3_KNN_TUNING_PATH), X_test_clasicas)
    # H1
    try:
        extractor_h1 = tf.keras.models.load_model(CNN_EXTRACTOR_PATH)
        svm_cnn = joblib.load(CNN_SVM_PATH)
        X_test_cnn = np.array([
            img_to_array(Image.open(p).convert("RGB").resize(IMG_SIZE)) / 255.0
            for p in archivos_test
        ])
        t0 = time.perf_counter()
        feats_h1 = extractor_h1.predict(X_test_cnn, verbose=0)
        t_inf_h1 = round((time.perf_counter() - t0) / n_test * 1000, 4)
        y_prob_h1 = svm_cnn.predict_proba(feats_h1)
        y_pred_h1 = svm_cnn.predict(feats_h1)
        acc = accuracy_score(y_true, y_pred_h1)
        mcc = matthews_corrcoef(y_true, y_pred_h1)
        modelos_eval.append({
            "nombre": "H1 - CNN + SVM",
            "y_pred": y_pred_h1,
            "y_prob": y_prob_h1,
            "accuracy": round(acc, 4),
            "balanced_accuracy": round(balanced_accuracy_score(y_true, y_pred_h1), 4),
            "precision": round(precision_score(y_true, y_pred_h1, average="macro", zero_division=0), 4),
            "recall": round(recall_score(y_true, y_pred_h1, average="macro", zero_division=0), 4),
            "f1_score": round(f1_score(y_true, y_pred_h1, average="macro", zero_division=0), 4),
            "f1_score_raw": f1_score(y_true, y_pred_h1, average="macro", zero_division=0),
            "mcc": round(mcc, 4),
            "tiempo_inferencia_ms": t_inf_h1,
        })
        print(f"  ✅ H1 - CNN + SVM | Acc: {acc:.4f} | MCC: {mcc:.4f}")
    except Exception as e:
        print(f"  ⚠️  H1 - CNN + SVM: {e}")
    # H2
    try:
        extractor_h2 = tf.keras.models.load_model(H2_EXTRACTOR_TUNING_PATH)
        rf_h2 = joblib.load(H2_RF_TUNING_PATH)
        X_test_h2 = extraer_embeddings_desde_archivos(archivos_test, extractor_h2)
        y_prob_h2 = rf_h2.predict_proba(X_test_h2)
        y_pred_h2 = rf_h2.predict(X_test_h2)
        t_inf_h2 = _medir_inferencia(rf_h2, X_test_h2)
        acc = accuracy_score(y_true, y_pred_h2)
        mcc = matthews_corrcoef(y_true, y_pred_h2)
        modelos_eval.append({
            "nombre": "H2 - MobileNetV2 + RF",
            "y_pred": y_pred_h2,
            "y_prob": y_prob_h2,
            "accuracy": round(acc, 4),
            "balanced_accuracy": round(balanced_accuracy_score(y_true, y_pred_h2), 4),
            "precision": round(precision_score(y_true, y_pred_h2, average="macro", zero_division=0), 4),
            "recall": round(recall_score(y_true, y_pred_h2, average="macro", zero_division=0), 4),
            "f1_score": round(f1_score(y_true, y_pred_h2, average="macro", zero_division=0), 4),
            "f1_score_raw": f1_score(y_true, y_pred_h2, average="macro", zero_division=0),
            "mcc": round(mcc, 4),
            "tiempo_inferencia_ms": t_inf_h2,
        })
        print(f"  ✅ H2 - MobileNetV2 + RF | Acc: {acc:.4f} | MCC: {mcc:.4f}")
    except Exception as e:
        print(f"  ⚠️  H2 - MobileNetV2 + RF: {e}")

    if not modelos_eval:
        print("\n⚠️  No se pudo evaluar ningún modelo.")
        return

    # ── Calcular AUC ───────────────────────────────────────────────
    for m in modelos_eval:
        y_b = label_binarize(y_true, classes=range(n_classes))
        try:
            fpr_micro, tpr_micro, _ = roc_curve(y_b.ravel(), m["y_prob"].ravel())
            m["auc_micro"] = round(auc(fpr_micro, tpr_micro), 4)
            tpr_list = []
            for i in range(n_classes):
                fpr_i, tpr_i, _ = roc_curve(y_b[:, i], m["y_prob"][:, i])
                tpr_list.append(np.interp(np.linspace(0, 1, 100), fpr_i, tpr_i))
            m["auc_macro"] = round(auc(np.linspace(0, 1, 100), np.mean(tpr_list, axis=0)), 4)
        except Exception:
            m["auc_micro"] = None
            m["auc_macro"] = None

    # ── Ranking unificado: MCC → F1-macro → Accuracy ───────────────
    filas = []
    for m in modelos_eval:
        filas.append({k: v for k, v in m.items() if k not in ("y_pred", "y_prob")})
    comparativa = pd.DataFrame(filas)
    comparativa = comparativa.sort_values(
        by=["mcc", "f1_score", "accuracy"],
        ascending=[False, False, False],
    ).reset_index(drop=True)
    comparativa["ranking"] = range(1, len(comparativa) + 1)
    cols = [
        "ranking", "nombre", "accuracy", "balanced_accuracy",
        "precision", "recall", "f1_score", "mcc",
        "auc_macro", "auc_micro", "tiempo_inferencia_ms",
    ]
    cols = [c for c in cols if c in comparativa.columns]
    comparativa = comparativa[cols]

    # Renombrar nombre -> modelo para archivo de salida
    cmp_out = comparativa.rename(columns={"nombre": "modelo"})
    cmp_path = COMPARATIVOS_DIR / "comparacion_general_modelos.csv"
    cmp_out.to_csv(cmp_path, index=False, float_format="%.4f")
    print(f"\n✅ Comparación general guardada: {cmp_path}")
    print("\n" + cmp_out.to_string(index=False))

    # ══════════════════════════════════════════════════════════════════
    # F1 por clase
    # ══════════════════════════════════════════════════════════════════
    print("\n" + "=" * 60)
    print("  F1 POR CLASE — Desglose por categoría")
    print("=" * 60)

    from sklearn.metrics import classification_report

    orden = comparativa["nombre"].tolist()
    nombre_a_pred = {m["nombre"]: m["y_pred"] for m in modelos_eval}

    filas_f1 = []
    for nombre in orden:
        y_pred = nombre_a_pred.get(nombre)
        if y_pred is None:
            continue
        reporte = classification_report(
            y_true,
            y_pred,
            labels=range(n_classes),
            target_names=CLASS_NAMES,
            output_dict=True,
            zero_division=0,
        )
        fila = {"modelo": nombre}
        f1_raw_list = []
        for cls in CLASS_NAMES:
            f1_raw = reporte[cls]["f1-score"]
            fila[cls] = round(f1_raw, 4)
            f1_raw_list.append(f1_raw)
        f1_macro_calculado_raw = sum(f1_raw_list) / len(f1_raw_list)

        # Validación contra f1_score general (valores sin redondear)
        f1_general_raw = None
        for m in modelos_eval:
            if m["nombre"] == nombre:
                f1_general_raw = m["f1_score_raw"]
                break
        if f1_general_raw is not None:
            if not np.isclose(f1_macro_calculado_raw, f1_general_raw, atol=1e-10):
                raise ValueError(
                    f"Inconsistencia en {nombre}: "
                    f"F1-macro calculado={f1_macro_calculado_raw:.10f}, "
                    f"F1-macro general={f1_general_raw:.10f}"
                )

        fila["f1_macro_calculado"] = round(f1_macro_calculado_raw, 4)
        filas_f1.append(fila)

    if filas_f1:
        df_f1 = pd.DataFrame(filas_f1)
        f1_path = COMPARATIVOS_DIR / "comparacion_f1_por_clase.csv"
        df_f1.to_csv(f1_path, index=False)
        print(f"✅ F1 por clase guardado: {f1_path}")
        print("\n" + df_f1.to_string(index=False))

    # ══════════════════════════════════════════════════════════════════
    # ROC superpuestas
    # ══════════════════════════════════════════════════════════════════
    if len(modelos_eval) >= 2:
        fig, ax = plt.subplots(figsize=(9, 8))
        colors = ["#e74c3c", "#3498db", "#2ecc71", "#f39c12", "#9b59b6"]
        linestyles = ["-", "--", "-.", ":", (0, (3, 1, 1, 1))]

        for idx, m in enumerate(modelos_eval):
            y_b = label_binarize(y_true, classes=range(n_classes))
            fpr_micro, tpr_micro, _ = roc_curve(y_b.ravel(), m["y_prob"].ravel())
            auc_micro = auc(fpr_micro, tpr_micro)
            color = colors[idx % len(colors)]
            ls = linestyles[idx % len(linestyles)]
            ax.plot(fpr_micro, tpr_micro, color=color, ls=ls, lw=2,
                    label=f"{m['nombre']} (micro-AUC={auc_micro:.3f})")

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
    else:
        print("\n⚠️  No hay suficientes modelos para graficar ROC.")

    print("\n✅ Evaluación comparativa completada.")


if __name__ == "__main__":
    main()
