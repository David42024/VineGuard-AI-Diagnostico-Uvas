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


def save_roc_curves(y_test, y_score, class_names, save_path):
    n_classes = len(class_names)
    y_bin = label_binarize(y_test, classes=range(n_classes))
    if y_score.shape[1] != n_classes:
        print("  ⚠️  ROC: y_score no coincide con n_classes, se omite")
        return
    fpr, tpr, roc_auc = {}, {}, {}
    for i in range(n_classes):
        fpr[i], tpr[i], _ = roc_curve(y_bin[:, i], y_score[:, i])
        roc_auc[i] = auc(fpr[i], tpr[i])
    fpr["micro"], tpr["micro"], _ = roc_curve(y_bin.ravel(), y_score.ravel())
    roc_auc["micro"] = auc(fpr["micro"], tpr["micro"])
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
