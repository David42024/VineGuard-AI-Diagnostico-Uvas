"""
evaluacion_visual.py
─────────────────────
Utilidades para generar gráficos de evaluación de modelos:
  - Matriz de confusión (PNG)
  - Curvas ROC AUC (multiclase)
"""

import sys
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.metrics import (
    confusion_matrix,
    roc_curve,
    auc,
    roc_auc_score,
    precision_recall_curve,
    average_precision_score,
)
from sklearn.preprocessing import label_binarize


def save_confusion_matrix(y_test, y_pred, class_names, save_path):
    cm = confusion_matrix(y_test, y_pred)
    fig, ax = plt.subplots(figsize=(6, 5))
    im = ax.imshow(cm, interpolation="nearest", cmap="Blues")
    ax.figure.colorbar(im, ax=ax)
    ax.set(
        xticks=np.arange(len(class_names)),
        yticks=np.arange(len(class_names)),
        xticklabels=class_names,
        yticklabels=class_names,
        xlabel="Predicción",
        ylabel="Real",
    )
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")
    thresh = cm.max() / 2.0
    for i in range(len(class_names)):
        for j in range(len(class_names)):
            ax.text(j, i, format(cm[i, j], "d"),
                    ha="center", va="center",
                    color="white" if cm[i, j] > thresh else "black")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  📊 Matriz de confusión guardada: {save_path}")


def save_normalized_confusion_matrix(y_test, y_pred, class_names, save_path):
    cm = confusion_matrix(y_test, y_pred)
    cm_normalized = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]
    fig, ax = plt.subplots(figsize=(6, 5))
    im = ax.imshow(cm_normalized, interpolation="nearest", cmap="Greens")
    ax.figure.colorbar(im, ax=ax)
    ax.set(
        xticks=np.arange(len(class_names)),
        yticks=np.arange(len(class_names)),
        xticklabels=class_names,
        yticklabels=class_names,
        xlabel="Predicción",
        ylabel="Real",
    )
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")
    thresh = cm_normalized.max() / 2.0
    for i in range(len(class_names)):
        for j in range(len(class_names)):
            ax.text(j, i, format(cm_normalized[i, j], ".2%"),
                    ha="center", va="center",
                    color="white" if cm_normalized[i, j] > thresh else "black")
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  📊 Matriz de confusión normalizada guardada: {save_path}")


def save_roc_curves(y_test, y_score, class_names, save_path):
    n_classes = len(class_names)
    y_bin = label_binarize(y_test, classes=range(n_classes))
    if y_score.shape[1] != n_classes:
        print("  ⚠️  ROC: y_score no coincide con n_classes, se omite")
        return {}, {}
    fpr, tpr, roc_auc = {}, {}, {}
    for i in range(n_classes):
        fpr[i], tpr[i], _ = roc_curve(y_bin[:, i], y_score[:, i])
        roc_auc[i] = auc(fpr[i], tpr[i])
    fpr["micro"], tpr["micro"], _ = roc_curve(y_bin.ravel(), y_score.ravel())
    roc_auc["micro"] = auc(fpr["micro"], tpr["micro"])
    roc_auc["macro"] = np.mean([roc_auc[i] for i in range(n_classes)])
    fig, ax = plt.subplots(figsize=(7, 6))
    colors = ["#e74c3c", "#f39c12", "#27ae60", "#3498db"]
    for i in range(n_classes):
        ax.plot(fpr[i], tpr[i], color=colors[i % len(colors)],
                lw=2, label=f"{class_names[i]} (AUC={roc_auc[i]:.3f})")
    ax.plot(fpr["micro"], tpr["micro"], "k--", lw=2,
            label=f"Micro-promedio (AUC={roc_auc['micro']:.3f})")
    ax.plot([0, 1], [0, 1], "gray", lw=1, linestyle=":")
    ax.set(xlim=[0.0, 1.0], ylim=[0.0, 1.05],
           xlabel="Tasa de Falsos Positivos (1 - Especificidad)",
           ylabel="Tasa de Verdaderos Positivos (Sensibilidad)")
    ax.set_title("Curvas ROC — One-vs-Rest")
    ax.legend(loc="lower right", fontsize=8)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  📈 Curvas ROC guardadas: {save_path}")

    # Guardar CSV de AUC por clase
    auc_path = save_path.with_name(save_path.stem.replace("roc_", "auc_")).with_suffix(".csv")
    import pandas as pd
    auc_rows = []
    for i in range(n_classes):
        auc_rows.append({"clase": class_names[i], "auc": round(roc_auc[i], 4)})
    auc_rows.append({"clase": "macro_promedio", "auc": round(roc_auc["macro"], 4)})
    auc_rows.append({"clase": "micro_promedio", "auc": round(roc_auc["micro"], 4)})
    pd.DataFrame(auc_rows).to_csv(auc_path, index=False)
    print(f"  📊 AUC por clase guardado: {auc_path}")

    return roc_auc, auc_path


def save_precision_recall_curves(y_test, y_score, class_names, save_path):
    n_classes = len(class_names)
    y_bin = label_binarize(y_test, classes=range(n_classes))
    if y_score.shape[1] != n_classes:
        print("  ⚠️  Precision-Recall: y_score no coincide con n_classes, se omite")
        return {}, {}
    precision, recall, ap = {}, {}, {}
    for i in range(n_classes):
        precision[i], recall[i], _ = precision_recall_curve(y_bin[:, i], y_score[:, i])
        ap[i] = average_precision_score(y_bin[:, i], y_score[:, i])
    ap["micro"] = average_precision_score(y_bin, y_score, average="micro")
    ap["macro"] = average_precision_score(y_bin, y_score, average="macro")

    fig, ax = plt.subplots(figsize=(7, 6))
    colors = ["#e74c3c", "#f39c12", "#27ae60", "#3498db"]
    for i in range(n_classes):
        ax.plot(recall[i], precision[i], color=colors[i % len(colors)],
                lw=2, label=f"{class_names[i]} (AP={ap[i]:.3f})")
    ax.set(xlim=[0.0, 1.0], ylim=[0.0, 1.05],
           xlabel="Recall (Sensibilidad)",
           ylabel="Precision")
    ax.set_title("Curvas Precision-Recall — One-vs-Rest")
    ax.legend(loc="lower left", fontsize=8)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  📈 Curvas Precision-Recall guardadas: {save_path}")

    # Guardar CSV de AP por clase
    ap_path = save_path.with_name(save_path.stem.replace("precision_recall_", "ap_")).with_suffix(".csv")
    import pandas as pd
    ap_rows = []
    for i in range(n_classes):
        ap_rows.append({"clase": class_names[i], "ap": round(ap[i], 4)})
    ap_rows.append({"clase": "macro_promedio", "ap": round(ap["macro"], 4)})
    ap_rows.append({"clase": "micro_promedio", "ap": round(ap["micro"], 4)})
    pd.DataFrame(ap_rows).to_csv(ap_path, index=False)
    print(f"  📊 AP por clase guardado: {ap_path}")

    return ap, ap_path


def save_predictions_csv(y_test, y_score, class_names, filenames, save_path):
    y_pred = y_score.argmax(axis=1)
    rows = []
    for i, fname in enumerate(filenames):
        row = {
            "archivo": Path(fname).name,
            "clase_real": class_names[y_test[i]],
            "clase_predicha": class_names[y_pred[i]],
        }
        for cls_idx, cls_name in enumerate(class_names):
            row[f"prob_{cls_name}"] = round(y_score[i, cls_idx], 6)
        row["correcto"] = y_test[i] == y_pred[i]
        rows.append(row)
    import pandas as pd
    df = pd.DataFrame(rows)
    df.to_csv(save_path, index=False)
    print(f"  📄 Predicciones individuales guardadas: {save_path}")
    return df
