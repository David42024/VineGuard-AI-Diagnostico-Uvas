"""
validacion_estadistica_modelos.py
Validación estadística robusta de modelos — VineGuard AI

Pruebas implementadas:
  1. McNemar (pares de modelos)
  2. Cochran's Q (múltiples modelos simultáneamente)
  3. Friedman (si hay resultados por folds)
  4. Post-hoc Nemenyi / Wilcoxon con corrección Holm
  5. Intervalos de confianza por bootstrap (95%)
  6. Tamaño del efecto
  7. Diebold-Mariano (complementario, no principal)
"""

import sys
import warnings
from pathlib import Path
from itertools import combinations

import numpy as np
import pandas as pd
from scipy import stats

from sklearn.metrics import accuracy_score, f1_score, matthews_corrcoef

warnings.filterwarnings("ignore")

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mantenedor import MODELS_DIR, MODELOS_DIR, ESTADISTICA_DIR, CLASS_NAMES, SCALER_PATH, TEST_DIR, IMG_SIZE

import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
elif hasattr(sys.stdout, 'buffer'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

ESTADISTICA_DIR.mkdir(parents=True, exist_ok=True)
MODELOS_DIR.mkdir(parents=True, exist_ok=True)

N_BOOTSTRAP = 1000
ALPHA = 0.05


def load_all_predictions():
    """Carga las predicciones de todos los modelos desde los reportes existentes.
    En un flujo completo, esto se obtendría ejecutando cada modelo sobre el test set.
    """
    from extract_features import load_features
    from sklearn.svm import SVC
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.neighbors import KNeighborsClassifier
    import joblib

    print("🔄 Cargando datos y generando predicciones de todos los modelos...")
    X_train, y_train, X_test, y_test = load_features(fit_scaler=False)
    X_train_s, X_test_s = X_train, X_test

    # Cargar scaler y re-escalar
    if SCALER_PATH.exists():
        scaler = joblib.load(SCALER_PATH)
        X_train_s = scaler.transform(X_train)
        X_test_s = scaler.transform(X_test)

    predicciones = {}
    nombres_modelos = []

    try:
        svm = joblib.load(MODELS_DIR / "svm_model.pkl")
        y_pred = svm.predict(X_test_s)
        predicciones["M1 - SVM"] = y_pred
        nombres_modelos.append("M1 - SVM")
        print("  ✅ M1 - SVM")
    except Exception as e:
        print(f"  ⚠️  M1 - SVM: {e}")

    try:
        rf = joblib.load(MODELS_DIR / "random_forest_model.pkl")
        y_pred = rf.predict(X_test_s)
        predicciones["M2 - Random Forest"] = y_pred
        nombres_modelos.append("M2 - Random Forest")
        print("  ✅ M2 - Random Forest")
    except Exception as e:
        print(f"  ⚠️  M2 - Random Forest: {e}")

    try:
        knn = joblib.load(MODELS_DIR / "knn_model.pkl")
        y_pred = knn.predict(X_test_s)
        predicciones["M3 - KNN"] = y_pred
        nombres_modelos.append("M3 - KNN")
        print("  ✅ M3 - KNN")
    except Exception as e:
        print(f"  ⚠️  M3 - KNN: {e}")

    try:
        import tensorflow as tf
        from tensorflow.keras.preprocessing.image import img_to_array
        from PIL import Image
        extractor = tf.keras.models.load_model(MODELS_DIR / "cnn_feature_extractor.h5")
        svm_cnn = joblib.load(MODELS_DIR / "cnn_svm_model.pkl")
        X_test_cnn = []
        for clase in CLASS_NAMES:
            d = TEST_DIR / clase
            for p in d.iterdir():
                if p.suffix.lower() in {".jpg", ".jpeg", ".png"}:
                    img = Image.open(p).convert("RGB").resize(IMG_SIZE)
                    arr = img_to_array(img) / 255.0
                    X_test_cnn.append(arr)
        X_test_cnn = np.array(X_test_cnn)
        feats = extractor.predict(X_test_cnn, verbose=0)
        y_pred = svm_cnn.predict(feats)
        predicciones["H1 - CNN+SVM"] = y_pred
        nombres_modelos.append("H1 - CNN+SVM")
        print("  ✅ H1 - CNN+SVM")
    except Exception as e:
        print(f"  ⚠️  H1 - CNN+SVM: {e}")

    try:
        import tensorflow as tf
        from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
        from PIL import Image
        extractor_t = tf.keras.models.load_model(MODELS_DIR / "transfer_feature_extractor.h5")
        rf_t = joblib.load(MODELS_DIR / "transfer_random_forest_model.pkl")
        X_test_t = []
        for clase in CLASS_NAMES:
            d = TEST_DIR / clase
            for p in d.iterdir():
                if p.suffix.lower() in {".jpg", ".jpeg", ".png"}:
                    img = tf.keras.utils.load_img(p, target_size=IMG_SIZE)
                    arr = tf.keras.utils.img_to_array(img)
                    arr = preprocess_input(arr)
                    X_test_t.append(arr)
        X_test_t = np.array(X_test_t)
        feats_t = extractor_t.predict(X_test_t, verbose=0)
        y_pred = rf_t.predict(feats_t)
        predicciones["H2 - MobileNetV2+RF"] = y_pred
        nombres_modelos.append("H2 - MobileNetV2+RF")
        print("  ✅ H2 - MobileNetV2+RF")
    except Exception as e:
        print(f"  ⚠️  H2 - MobileNetV2+RF: {e}")

    return y_test, predicciones, nombres_modelos


# ══════════════════════════════════════════════════════════════════════════════
#  1. PRUEBA DE MCNEMAR
# ══════════════════════════════════════════════════════════════════════════════

def mcnemar_test(y_true, y_pred1, y_pred2):
    correct_1 = (y_true == y_pred1)
    correct_2 = (y_true == y_pred2)
    b = np.sum(correct_1 & ~correct_2)
    c = np.sum(~correct_1 & correct_2)
    if b + c == 0:
        return {"b": 0, "c": 0, "statistic": 0.0, "p_value": 1.0,
                "interpretation": "No hay diferencias entre modelos"}
    stat = (abs(b - c) - 0.5) ** 2 / (b + c) if b + c > 25 else (b - c) ** 2 / (b + c)
    p = 1 - stats.chi2.cdf(stat, df=1)
    if p < 0.001:
        interp = "Diferencia altamente significativa (p < 0.001)"
    elif p < 0.01:
        interp = "Diferencia muy significativa (p < 0.01)"
    elif p < 0.05:
        interp = "Diferencia significativa (p < 0.05)"
    else:
        interp = "No hay diferencia significativa (p >= 0.05)"
    return {"b": int(b), "c": int(c), "statistic": round(stat, 4), "p_value": round(p, 4),
            "interpretation": interp}


def ejecutar_mcnemar(y_true, predicciones, nombres):
    print("\n" + "=" * 60)
    print("  1. PRUEBA DE MCNEMAR — Comparaciones por pares")
    print("=" * 60)
    resultados = []
    for (n1, p1), (n2, p2) in combinations(zip(nombres, [predicciones[n] for n in nombres]), 2):
        res = mcnemar_test(y_true, p1, p2)
        res["modelo_1"] = n1
        res["modelo_2"] = n2
        resultados.append(res)
        print(f"\n  {n1} vs {n2}")
        print(f"    b={res['b']}, c={res['c']}, χ²={res['statistic']}, p={res['p_value']}")
        print(f"    → {res['interpretation']}")
    df = pd.DataFrame(resultados)
    df.to_csv(ESTADISTICA_DIR / "mcnemar_resultados.csv", index=False)
    print(f"\n  ✅ Guardado: {ESTADISTICA_DIR / 'mcnemar_resultados.csv'}")
    return df


# ══════════════════════════════════════════════════════════════════════════════
#  2. PRUEBA DE COCHRAN'S Q
# ══════════════════════════════════════════════════════════════════════════════

def cochran_q_test(y_true, predicciones, nombres):
    print("\n" + "=" * 60)
    print("  2. PRUEBA DE COCHRAN'S Q — Comparación simultánea")
    print("=" * 60)
    n = len(y_true)
    k = len(nombres)
    aciertos = np.array([(y_true == predicciones[n]).astype(int) for n in nombres])
    N = n
    suma_filas = aciertos.sum(axis=0)
    suma_columnas = aciertos.sum(axis=1)
    suma_total = suma_columnas.sum()

    Q = (k * (k - 1) * np.sum((suma_columnas - suma_total / k) ** 2)) / \
        (k * suma_total - np.sum(suma_filas ** 2)) if (k * suma_total - np.sum(suma_filas ** 2)) != 0 else 0

    p_value = 1 - stats.chi2.cdf(Q, df=k - 1)
    interp = "Diferencias significativas entre modelos" if p_value < ALPHA else \
             "No hay diferencias significativas entre modelos"

    print(f"  Estadístico Q: {Q:.4f}")
    print(f"  p-value: {p_value:.4f}")
    print(f"  Interpretación: {interp}")

    resultado = {"estadistico_Q": round(Q, 4), "p_value": round(p_value, 4),
                 "interpretacion": interp, "k": k, "n": n}
    pd.DataFrame([resultado]).to_csv(ESTADISTICA_DIR / "cochran_q_resultado.csv", index=False)
    print(f"  ✅ Guardado: {ESTADISTICA_DIR / 'cochran_q_resultado.csv'}")
    return resultado


# ══════════════════════════════════════════════════════════════════════════════
#  3. PRUEBA DE FRIEDMAN
# ══════════════════════════════════════════════════════════════════════════════

def friedman_test(y_true, predicciones, nombres):
    print("\n" + "=" * 60)
    print("  3. PRUEBA DE FRIEDMAN — Comparación por rankings")
    print("=" * 60)
    n = len(y_true)
    k = len(nombres)
    if k < 2:
        print("  ⚠️  Se requieren al menos 2 modelos.")
        return None
    errores = np.array([(y_true != predicciones[n]).astype(float) for n in nombres])
    rankings = np.argsort(errores, axis=0).astype(float) + 1
    ranks_avg = rankings.mean(axis=1)
    denom = n * k * (k + 1) / 6
    suma_rank_sq = np.sum(ranks_avg ** 2)
    friedman_stat = 12 * n / (k * (k + 1)) * (np.sum(ranks_avg ** 2) - k * (k + 1) ** 2 / 4)
    p_value = 1 - stats.chi2.cdf(friedman_stat, df=k - 1)

    print(f"  Estadístico de Friedman: {friedman_stat:.4f}")
    print(f"  p-value: {p_value:.4f}")
    for i, n in enumerate(nombres):
        print(f"    Ranking promedio {n}: {ranks_avg[i]:.4f}")

    interp = "Diferencias significativas entre modelos" if p_value < ALPHA else \
             "No hay diferencias significativas entre modelos"
    print(f"  Interpretación: {interp}")

    resultado = {"estadistico_Friedman": round(friedman_stat, 4), "p_value": round(p_value, 4),
                 "interpretacion": interp}
    pd.DataFrame([resultado]).to_csv(ESTADISTICA_DIR / "friedman_resultado.csv", index=False)
    print(f"  ✅ Guardado: {ESTADISTICA_DIR / 'friedman_resultado.csv'}")
    return resultado, ranks_avg


# ══════════════════════════════════════════════════════════════════════════════
#  4. POST-HOC: WILCOXON CON CORRECCIÓN HOLM
# ══════════════════════════════════════════════════════════════════════════════

def posthoc_wilcoxon(y_true, predicciones, nombres):
    print("\n" + "=" * 60)
    print("  4. POST-HOC: Wilcoxon Signed-Rank con corrección Holm")
    print("=" * 60)
    resultados = []
    comparaciones = list(combinations(range(len(nombres)), 2))
    p_values = []
    for i, j in comparaciones:
        n1, n2 = nombres[i], nombres[j]
        err1 = (y_true != predicciones[n1]).astype(int)
        err2 = (y_true != predicciones[n2]).astype(int)
        diff = err1 - err2
        mask = diff != 0
        if mask.sum() < 2:
            p_val = 1.0
        else:
            _, p_val = stats.wilcoxon(err1[mask], err2[mask], alternative="two-sided")
        p_values.append({"i": i, "j": j, "n1": n1, "n2": n2, "p_raw": p_val})

    # Corrección Holm
    m = len(p_values)
    p_vals = [pv["p_raw"] for pv in p_values]
    sorted_idx = np.argsort(p_vals)
    reject = [False] * m
    for rank, idx in enumerate(sorted_idx):
        adj_alpha = ALPHA / (m - rank)
        if p_vals[idx] < adj_alpha:
            reject[idx] = True
        else:
            break

    for pv, rej in zip(p_values, reject):
        pv["p_corregido_Holm"] = min(pv["p_raw"] * (m - sorted_idx.tolist().index(p_values.index(pv))), 1.0)
        pv["significativo"] = "Sí" if rej else "No"
        print(f"  {pv['n1']} vs {pv['n2']}: p_raw={pv['p_raw']:.4f}, p_holm={pv['p_corregido_Holm']:.4f}, Significativo: {pv['significativo']}")
        resultados.append(pv)

    df = pd.DataFrame(resultados)
    df.to_csv(ESTADISTICA_DIR / "wilcoxon_posthoc.csv", index=False)
    print(f"  ✅ Guardado: {ESTADISTICA_DIR / 'wilcoxon_posthoc.csv'}")
    return df


# ══════════════════════════════════════════════════════════════════════════════
#  5. INTERVALOS DE CONFIANZA POR BOOTSTRAP
# ══════════════════════════════════════════════════════════════════════════════

def bootstrap_ci(y_true, predicciones, nombres, n_bootstrap=N_BOOTSTRAP):
    print("\n" + "=" * 60)
    print(f"  5. INTERVALOS DE CONFIANZA POR BOOTSTRAP ({n_bootstrap} remuestreos)")
    print("=" * 60)
    resultados = []
    for nombre in nombres:
        y_pred = predicciones[nombre]
        acc_boot, f1_boot, mcc_boot = [], [], []
        n = len(y_true)
        np.random.seed(42)
        for _ in range(n_bootstrap):
            idx = np.random.randint(0, n, n)
            yt_boot = y_true[idx]
            yp_boot = y_pred[idx]
            acc_boot.append(accuracy_score(yt_boot, yp_boot))
            f1_boot.append(f1_score(yt_boot, yp_boot, average="macro", zero_division=0))
            mcc_boot.append(matthews_corrcoef(yt_boot, yp_boot))
        acc_ci = (round(np.percentile(acc_boot, 2.5), 4), round(np.percentile(acc_boot, 97.5), 4))
        f1_ci = (round(np.percentile(f1_boot, 2.5), 4), round(np.percentile(f1_boot, 97.5), 4))
        mcc_ci = (round(np.percentile(mcc_boot, 2.5), 4), round(np.percentile(mcc_boot, 97.5), 4))
        resultados.append({
            "modelo": nombre,
            "acc_media": round(np.mean(acc_boot), 4),
            "acc_ci_inf": acc_ci[0], "acc_ci_sup": acc_ci[1],
            "f1_media": round(np.mean(f1_boot), 4),
            "f1_ci_inf": f1_ci[0], "f1_ci_sup": f1_ci[1],
            "mcc_media": round(np.mean(mcc_boot), 4),
            "mcc_ci_inf": mcc_ci[0], "mcc_ci_sup": mcc_ci[1],
        })
        print(f"  {nombre}:")
        print(f"    Accuracy: {resultados[-1]['acc_media']:.4f}  IC95% [{acc_ci[0]:.4f}, {acc_ci[1]:.4f}]")
        print(f"    F1-macro: {resultados[-1]['f1_media']:.4f}  IC95% [{f1_ci[0]:.4f}, {f1_ci[1]:.4f}]")
        print(f"    MCC:      {resultados[-1]['mcc_media']:.4f}  IC95% [{mcc_ci[0]:.4f}, {mcc_ci[1]:.4f}]")

    df = pd.DataFrame(resultados)
    df.to_csv(ESTADISTICA_DIR / "intervalos_confianza_bootstrap.csv", index=False)
    print(f"  ✅ Guardado: {ESTADISTICA_DIR / 'intervalos_confianza_bootstrap.csv'}")
    return df


# ══════════════════════════════════════════════════════════════════════════════
#  6. TAMAÑO DEL EFECTO
# ══════════════════════════════════════════════════════════════════════════════

def tamano_efecto(y_true, predicciones, nombres):
    print("\n" + "=" * 60)
    print("  6. TAMAÑO DEL EFECTO")
    print("=" * 60)
    resultados = []
    for (n1, p1), (n2, p2) in combinations(zip(nombres, [predicciones[n] for n in nombres]), 2):
        acc1 = accuracy_score(y_true, p1)
        acc2 = accuracy_score(y_true, p2)
        f1_1 = f1_score(y_true, p1, average="macro", zero_division=0)
        f1_2 = f1_score(y_true, p2, average="macro", zero_division=0)
        mcc1 = matthews_corrcoef(y_true, p1)
        mcc2 = matthews_corrcoef(y_true, p2)
        diff_acc = abs(acc1 - acc2)
        diff_f1 = abs(f1_1 - f1_2)
        diff_mcc = abs(mcc1 - mcc2)
        correct_1 = (y_true == p1)
        correct_2 = (y_true == p2)
        b = np.sum(correct_1 & ~correct_2)
        c = np.sum(~correct_1 & correct_2)
        odds_ratio = (b / c) if c > 0 else float("inf")
        resultados.append({
            "modelo_1": n1, "modelo_2": n2,
            "diff_accuracy": round(diff_acc, 4),
            "diff_f1_macro": round(diff_f1, 4),
            "diff_mcc": round(diff_mcc, 4),
            "odds_ratio_mcnemar": round(odds_ratio, 4) if odds_ratio != float("inf") else "inf",
        })
        print(f"  {n1} vs {n2}: ΔAcc={diff_acc:.4f}, ΔF1={diff_f1:.4f}, ΔMCC={diff_mcc:.4f}")
    df = pd.DataFrame(resultados)
    df.to_csv(ESTADISTICA_DIR / "tamano_efecto.csv", index=False)
    print(f"  ✅ Guardado: {ESTADISTICA_DIR / 'tamano_efecto.csv'}")
    return df


# ══════════════════════════════════════════════════════════════════════════════
#  7. DIEBOLD-MARIANO (COMPLEMENTARIO)
# ══════════════════════════════════════════════════════════════════════════════

def diebold_mariano_complementario(y_true, predicciones, nombres):
    print("\n" + "=" * 60)
    print("  7. DIEBOLD-MARIANO (Complementario — no es la prueba principal)")
    print("=" * 60)
    print("""
  NOTA: Diebold-Mariano se diseñó para comparar precisión de pronósticos
  en series temporales. En clasificación de imágenes NO es la prueba
  recomendada. Se incluye aquí solo como análisis complementario.

  Las pruebas principales para este proyecto son:
    • McNemar (comparación por pares)
    • Cochran's Q (comparación simultánea)
    • Friedman + post-hoc Nemenyi/Wilcoxon
    • Intervalos de confianza bootstrap
    • MCC y matriz de confusión
  """)
    # Implementación adaptada: comparación de errores cuadráticos
    resultados = []
    for (n1, p1), (n2, p2) in combinations(zip(nombres, [predicciones[n] for n in nombres]), 2):
        err1 = (y_true != p1).astype(float)
        err2 = (y_true != p2).astype(float)
        d = err1 - err2
        mean_d = np.mean(d)
        var_d = np.var(d, ddof=1) if len(d) > 1 else 0
        dm_stat = mean_d / np.sqrt(var_d / len(d)) if var_d > 0 else 0
        p_val = 2 * (1 - stats.norm.cdf(abs(dm_stat)))
        resultados.append({
            "modelo_1": n1, "modelo_2": n2,
            "DM_statistic": round(dm_stat, 4), "p_value": round(p_val, 4),
        })
        print(f"  {n1} vs {n2}: DM={dm_stat:.4f}, p={p_val:.4f}")
    df = pd.DataFrame(resultados)
    df.to_csv(ESTADISTICA_DIR / "diebold_mariano_complementario.csv", index=False)
    print(f"  ✅ Guardado (complementario): {ESTADISTICA_DIR / 'diebold_mariano_complementario.csv'}")
    return df


def main():
    print("\n" + "=" * 60)
    print("  VALIDACIÓN ESTADÍSTICA DE MODELOS — VineGuard AI")
    print("=" * 60)

    y_true, predicciones, nombres = load_all_predictions()
    if len(nombres) < 2:
        print("\n⚠️  No hay suficientes modelos para comparar.")
        return

    print(f"\n📊 Total muestras de prueba: {len(y_true)}")
    print(f"📊 Modelos disponibles: {', '.join(nombres)}")

    # 1. McNemar
    ejecutar_mcnemar(y_true, predicciones, nombres)

    # 2. Cochran's Q
    cochran_q_test(y_true, predicciones, nombres)

    # 3. Friedman
    friedman_result = friedman_test(y_true, predicciones, nombres)

    # 4. Post-hoc Wilcoxon
    posthoc_wilcoxon(y_true, predicciones, nombres)

    # 5. Bootstrap CI
    bootstrap_ci(y_true, predicciones, nombres)

    # 6. Tamaño del efecto
    tamano_efecto(y_true, predicciones, nombres)

    # 7. Diebold-Mariano (complementario)
    diebold_mariano_complementario(y_true, predicciones, nombres)

    print("\n" + "=" * 60)
    print("  ✅ Validación estadística completada")
    print(f"  Reportes guardados en: {ESTADISTICA_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()
