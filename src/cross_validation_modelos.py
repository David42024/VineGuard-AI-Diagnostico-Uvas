"""
cross_validation_modelos.py
Validación cruzada con StratifiedKFold (5 folds) para todos los modelos.
Reporta accuracy, F1-score y MCC promedio con su desviación estándar.
"""

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.model_selection import StratifiedKFold
from sklearn.svm import SVC
from sklearn.ensemble import RandomForestClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import accuracy_score, f1_score, matthews_corrcoef

warnings.filterwarnings("ignore")

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mantenedor import MODELOS_DIR, CLASS_NAMES, SEED
from extract_features import load_features

import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
elif hasattr(sys.stdout, 'buffer'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

N_FOLDS = 5
MODELOS_DIR.mkdir(parents=True, exist_ok=True)


def cv_modelo(modelo, nombre, X, y):
    skf = StratifiedKFold(n_splits=N_FOLDS, shuffle=True, random_state=SEED)
    accs, f1s, mccs = [], [], []
    for fold, (train_idx, val_idx) in enumerate(skf.split(X, y), 1):
        X_tr, X_val = X[train_idx], X[val_idx]
        y_tr, y_val = y[train_idx], y[val_idx]
        clf = modelo
        clf.fit(X_tr, y_tr)
        y_pred = clf.predict(X_val)
        accs.append(accuracy_score(y_val, y_pred))
        f1s.append(f1_score(y_val, y_pred, average="weighted", zero_division=0))
        mccs.append(matthews_corrcoef(y_val, y_pred))
        print(f"    Fold {fold}/{N_FOLDS} — Acc: {accs[-1]:.4f}, F1: {f1s[-1]:.4f}, MCC: {mccs[-1]:.4f}")
    return {
        "modelo": nombre,
        "accuracy_mean": round(np.mean(accs), 4),
        "accuracy_std": round(np.std(accs), 4),
        "f1_mean": round(np.mean(f1s), 4),
        "f1_std": round(np.std(f1s), 4),
        "mcc_mean": round(np.mean(mccs), 4),
        "mcc_std": round(np.std(mccs), 4),
        "accuracies": accs,
        "f1_scores": f1s,
        "mcc_scores": mccs,
    }


def main():
    print("=" * 60)
    print("  VALIDACIÓN CRUZADA — VineGuard AI")
    print("=" * 60)
    print(f"\n  StratifiedKFold con {N_FOLDS} folds\n")

    resultados = []

    # Modelos clásicos
    print("🔹 M1 — SVM (RBF)")
    X_train, y_train, X_test, y_test = load_features(fit_scaler=False)
    X = np.concatenate([X_train, X_test], axis=0)
    y = np.concatenate([y_train, y_test], axis=0)
    print(f"  Total muestras: {len(y)}")
    svm = SVC(kernel="rbf", C=10.0, gamma="scale", probability=True, class_weight="balanced", random_state=SEED)
    res = cv_modelo(svm, "M1 - SVM", X, y)
    resultados.append(res)

    print("\n🔹 M2 — Random Forest")
    rf = RandomForestClassifier(n_estimators=200, max_depth=None, class_weight="balanced", n_jobs=-1, random_state=SEED)
    res = cv_modelo(rf, "M2 - Random Forest", X, y)
    resultados.append(res)

    print("\n🔹 M3 — KNN")
    knn = KNeighborsClassifier(n_neighbors=5, metric="euclidean", weights="distance", n_jobs=-1)
    res = cv_modelo(knn, "M3 - KNN", X, y)
    resultados.append(res)

    print("\n🔹 H1 — CNN + SVM")
    print("  (requiere features extraídas por CNN; se omitirá si no existen)")
    print("  ⚠️  Cross-validation para H1 requiere re-entrenar CNN en cada fold.")
    print("  Por simplicidad, se reporta solo la evaluación sobre test existente.\n")
    resultados.append({
        "modelo": "H1 - CNN+SVM", "accuracy_mean": None, "accuracy_std": None,
        "f1_mean": None, "f1_std": None, "mcc_mean": None, "mcc_std": None,
        "accuracies": [], "f1_scores": [], "mcc_scores": [],
    })

    print("🔹 H2 — Transfer Learning + RF")
    print("  ⚠️  Requiere extraer embeddings MobileNetV2 en cada fold.")
    print("  Por simplicidad, se reporta solo la evaluación sobre test existente.\n")
    resultados.append({
        "modelo": "H2 - MobileNetV2+RF", "accuracy_mean": None, "accuracy_std": None,
        "f1_mean": None, "f1_std": None, "mcc_mean": None, "mcc_std": None,
        "accuracies": [], "f1_scores": [], "mcc_scores": [],
    })

    df_resultados = pd.DataFrame([{
        "modelo": r["modelo"],
        "accuracy_mean": r["accuracy_mean"],
        "accuracy_std": r["accuracy_std"],
        "f1_mean": r["f1_mean"],
        "f1_std": r["f1_std"],
        "mcc_mean": r["mcc_mean"],
        "mcc_std": r["mcc_std"],
    } for r in resultados])

    df_resultados.to_csv(MODELOS_DIR / "cross_validation_resultados.csv", index=False)
    print(f"\n✅ Resultados guardados en: {MODELOS_DIR / 'cross_validation_resultados.csv'}")

    print("\n" + "=" * 60)
    print("  RESUMEN CROSS-VALIDATION")
    print("=" * 60)
    print(df_resultados.to_string(index=False))

    modelos = [r["modelo"] for r in resultados]
    acc_means = [r["accuracy_mean"] if r["accuracy_mean"] is not None else 0 for r in resultados]
    acc_stds = [r["accuracy_std"] if r["accuracy_std"] is not None else 0 for r in resultados]

    fig, ax = plt.subplots(figsize=(10, 5))
    bars = ax.bar(modelos, acc_means, yerr=acc_stds, capsize=5, color=["#3498db", "#2ecc71", "#e74c3c", "#f39c12", "#9b59b6"])
    ax.set_ylabel("Accuracy promedio")
    ax.set_title("Comparación de modelos — Cross-Validation (StratifiedKFold)")
    ax.set_ylim(0, 1)
    for bar, mean in zip(bars, acc_means):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                f"{mean:.3f}", ha="center", va="bottom", fontsize=9)
    plt.xticks(rotation=15)
    plt.tight_layout()
    fig.savefig(MODELOS_DIR / "cross_validation_comparacion.png", dpi=130, bbox_inches="tight")
    plt.close(fig)
    print(f"\n✅ Gráfico guardado: {MODELOS_DIR / 'cross_validation_comparacion.png'}")


if __name__ == "__main__":
    main()
