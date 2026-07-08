"""
seleccion_mejor_modelo.py
Selección del mejor modelo basado en múltiples criterios.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mantenedor import MODELOS_DIR, ESTADISTICA_DIR, CLASS_NAMES

import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
elif hasattr(sys.stdout, 'buffer'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

MODELOS_DIR.mkdir(parents=True, exist_ok=True)
ESTADISTICA_DIR.mkdir(parents=True, exist_ok=True)


def cargar_resultados():
    resultados = []
    archivos = [
        ("M1 - SVM", MODELOS_DIR / "resultados_m1_svm.csv"),
        ("M2 - Random Forest", MODELOS_DIR / "resultados_m2_random_forest.csv"),
        ("M3 - KNN", MODELOS_DIR / "resultados_m3_knn.csv"),
        ("H1 - CNN+SVM", MODELOS_DIR / "resultados_h1_cnn_svm.csv"),
        ("H2 - MobileNetV2+RF", MODELOS_DIR / "resultados_h2_transfer_rf.csv"),
    ]
    for nombre, archivo in archivos:
        if archivo.exists():
            df = pd.read_csv(archivo)
            if not df.empty:
                row = df.iloc[0].to_dict()
                row["modelo"] = nombre
                resultados.append(row)
                print(f"  ✅ {nombre}: cargado desde {archivo.name}")
            else:
                print(f"  ⚠️  {nombre}: archivo vacío")
        else:
            print(f"  ⚠️  {nombre}: no encontrado ({archivo.name})")
    if resultados:
        return pd.DataFrame(resultados)
    bootstrap_file = ESTADISTICA_DIR / "intervalos_confianza_bootstrap.csv"
    if bootstrap_file.exists():
        print(f"\n  Usando resultados de validación estadística como respaldo: {bootstrap_file.name}")
        df_boot = pd.read_csv(bootstrap_file)
        for _, row in df_boot.iterrows():
            resultados.append({
                "modelo": row["modelo"],
                "accuracy": row["acc_media"],
                "f1_score": row["f1_media"],
                "mcc": row["mcc_media"],
            })
        return pd.DataFrame(resultados)
    return pd.DataFrame()


def cargar_cv():
    archivo = MODELOS_DIR / "cross_validation_resultados.csv"
    if archivo.exists():
        df = pd.read_csv(archivo)
        return df[df["accuracy_mean"].notna()] if not df.empty else pd.DataFrame()
    return pd.DataFrame()


def seleccionar_mejor(df_metricas, df_cv):
    print("\n" + "=" * 60)
    print("  SELECCIÓN DEL MEJOR MODELO — VineGuard AI")
    print("=" * 60)

    if df_metricas.empty:
        print("\n⚠️  No hay resultados de modelos para evaluar.")
        return

    # Calcular puntuación compuesta
    pesos = {"mcc": 0.30, "f1_score": 0.30, "accuracy": 0.25, "balanced_accuracy": 0.15}
    df = df_metricas.copy()

    for col in pesos:
        if col not in df.columns:
            print(f"  ⚠️  Columna {col} no encontrada. Se usará 0.")
            df[col] = 0.0

    # Normalizar cada métrica al rango [0, 1]
    for col in pesos:
        c = df[col].values.astype(float)
        c_min, c_max = c.min(), c.max()
        if c_max > c_min:
            df[f"{col}_norm"] = (c - c_min) / (c_max - c_min)
        else:
            df[f"{col}_norm"] = 0.5

    df["puntaje_compuesto"] = sum(
        df[f"{col}_norm"] * peso for col, peso in pesos.items()
    )

    # Penalización por tiempo de inferencia (si es similar)
    if "tiempo_inferencia_ms" in df.columns:
        tiempos = df["tiempo_inferencia_ms"].values.astype(float)
        t_min, t_max = tiempos.min(), tiempos.max()
        if t_max > t_min:
            df["penalizacion_tiempo"] = (tiempos - t_min) / (t_max - t_min) * 0.05
        else:
            df["penalizacion_tiempo"] = 0.0
        df["puntaje_final"] = df["puntaje_compuesto"] - df["penalizacion_tiempo"]
    else:
        df["puntaje_final"] = df["puntaje_compuesto"]

    # Ordenar por puntaje final
    df = df.sort_values("puntaje_final", ascending=False).reset_index(drop=True)
    df["ranking"] = range(1, len(df) + 1)

    # Mostrar ranking
    print("\n  RANKING DE MODELOS:")
    print("  " + "-" * 80)
    print(f"  {'Rank':<6} {'Modelo':<25} {'Acc':<8} {'F1':<8} {'MCC':<8} {'Puntaje':<10}")
    print("  " + "-" * 80)
    for _, row in df.iterrows():
        acc = f"{row.get('accuracy', 0):.4f}" if pd.notna(row.get('accuracy', None)) else "N/A"
        f1 = f"{row.get('f1_score', 0):.4f}" if pd.notna(row.get('f1_score', None)) else "N/A"
        mcc = f"{row.get('mcc', 0):.4f}" if pd.notna(row.get('mcc', None)) else "N/A"
        punt = f"{row['puntaje_final']:.4f}"
        print(f"  #{row['ranking']:<4} {row['modelo']:<25} {acc:<8} {f1:<8} {mcc:<8} {punt:<10}")

    # Seleccionar mejor modelo
    mejor = df.iloc[0]
    print("\n" + "=" * 60)
    print(f"  🏆 MEJOR MODELO SELECCIONADO")
    print("=" * 60)
    print(f"\n  Modelo: {mejor['modelo']}")
    if pd.notna(mejor.get("accuracy", None)):
        print(f"  Accuracy: {mejor['accuracy']:.4f}")
    if pd.notna(mejor.get("f1_score", None)):
        print(f"  F1-Score: {mejor['f1_score']:.4f}")
    if pd.notna(mejor.get("mcc", None)):
        print(f"  MCC: {mejor['mcc']:.4f}")
    if pd.notna(mejor.get("tiempo_inferencia_ms", None)):
        print(f"  Tiempo inferencia: {mejor['tiempo_inferencia_ms']:.2f} ms")

    # Justificación
    justificacion_puntos = []
    if pd.notna(mejor.get("mcc", None)):
        justificacion_puntos.append(f"- Obtuvo el mayor MCC ({mejor['mcc']:.4f})")
    if pd.notna(mejor.get("f1_score", None)):
        justificacion_puntos.append(f"- Obtuvo el mayor F1-Score ({mejor['f1_score']:.4f})")
    if pd.notna(mejor.get("accuracy", None)):
        justificacion_puntos.append(f"- Obtuvo el mayor accuracy ({mejor['accuracy']:.4f})")
    justificacion_puntos.append("- Presentó el mejor rendimiento del ranking compuesto")

    if not df_cv.empty and mejor["modelo"] in df_cv["modelo"].values:
        cv_row = df_cv[df_cv["modelo"] == mejor["modelo"]].iloc[0]
        if pd.notna(cv_row.get("accuracy_std", None)):
            justificacion_puntos.append(f"- Estabilidad en CV: {cv_row['accuracy_std']:.4f}")

    print("\n  Justificación:")
    for punto in justificacion_puntos:
        print(f"    {punto}")

    # Guardar resultados
    ranking_cols = ["ranking", "modelo", "accuracy", "f1_score", "mcc",
                    "balanced_accuracy", "puntaje_compuesto", "puntaje_final"]
    ranking_cols = [c for c in ranking_cols if c in df.columns]
    df_ranking = df[ranking_cols]
    df_ranking.to_csv(MODELOS_DIR / "ranking_modelos.csv", index=False)
    print(f"\n  ✅ Ranking guardado: {MODELOS_DIR / 'ranking_modelos.csv'}")

    mejor_texto = f"""Mejor modelo seleccionado: {mejor['modelo']}
Justificación:
{chr(10).join(justificacion_puntos)}
"""
    with open(MODELOS_DIR / "mejor_modelo.txt", "w", encoding="utf-8") as f:
        f.write(mejor_texto)
    print(f"  ✅ Mejor modelo guardado: {MODELOS_DIR / 'mejor_modelo.txt'}")

    # Graficar comparación
    fig, axes = plt.subplots(1, 3, figsize=(14, 4))
    modelos = df["modelo"].tolist()
    metricas = [
        ("accuracy", "Accuracy", "#3498db"),
        ("f1_score", "F1-Score", "#2ecc71"),
        ("mcc", "MCC", "#e74c3c"),
    ]
    for ax, (col, title, color) in zip(axes, metricas):
        if col in df.columns:
            vals = df[col].values.astype(float)
            bars = ax.bar(modelos, vals, color=color, alpha=0.8)
            ax.set_title(title, fontweight="bold")
            ax.set_ylim(0, 1)
            ax.tick_params(axis="x", rotation=15)
            for bar, v in zip(bars, vals):
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                        f"{v:.3f}", ha="center", va="bottom", fontsize=8)

    plt.suptitle("Comparación de Métricas por Modelo", fontweight="bold")
    plt.tight_layout()
    fig.savefig(MODELOS_DIR / "comparacion_metricas_modelos.png", dpi=130, bbox_inches="tight")
    plt.close(fig)
    print(f"  ✅ Gráfico guardado: {MODELOS_DIR / 'comparacion_metricas_modelos.png'}")

    return mejor


def main():
    print("=" * 60)
    print("  SELECCIÓN DEL MEJOR MODELO — VineGuard AI")
    print("=" * 60)

    df_metricas = cargar_resultados()
    df_cv = cargar_cv()
    mejor = seleccionar_mejor(df_metricas, df_cv)

    if mejor is not None:
        print(f"\n✅ Modelo recomendado para diagnóstico: {mejor['modelo']}")
    print("\n✅ Proceso completado.")


if __name__ == "__main__":
    main()
