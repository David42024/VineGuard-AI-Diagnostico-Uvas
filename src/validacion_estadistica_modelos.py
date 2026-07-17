"""
validacion_estadistica_modelos.py
Validación estadística robusta de modelos — VineGuard AI

Pruebas implementadas:
  1. McNemar (pares de modelos)
  2. Cochran's Q (múltiples modelos simultáneamente)
  3. Post-hoc McNemar con corrección Holm
  4. Intervalos de confianza por bootstrap estratificado (95%)
  5. Tamaño del efecto
  6. Diebold-Mariano (complementario, no principal)
"""

import sys
from pathlib import Path
from itertools import combinations

import numpy as np
import pandas as pd
from scipy import stats

from sklearn.metrics import accuracy_score, f1_score, matthews_corrcoef
from statsmodels.stats.contingency_tables import mcnemar as sm_mcnemar

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mantenedor import (
    MODELOS_DIR,
    ESTADISTICA_DIR,
    CLASS_NAMES,
    TEST_DIR,
    IMG_SIZE,
    M1_SVM_TUNING_PATH,
    M2_RF_TUNING_PATH,
    M3_KNN_TUNING_PATH,
    H2_RF_TUNING_PATH,
    H2_EXTRACTOR_TUNING_PATH,
    CNN_EXTRACTOR_PATH,
    CNN_SVM_PATH,
)
import joblib

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
elif hasattr(sys.stdout, 'buffer'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

ESTADISTICA_DIR.mkdir(parents=True, exist_ok=True)
MODELOS_DIR.mkdir(parents=True, exist_ok=True)

N_BOOTSTRAP = 1000
ALPHA = 0.05


def obtener_archivos_test():
    """Devuelve una lista ordenada y reproducible de archivos TEST y sus etiquetas."""
    if not TEST_DIR.is_dir():
        raise FileNotFoundError(f"No existe el directorio TEST: {TEST_DIR}")
    archivos = []
    etiquetas = []
    for indice_clase, clase in enumerate(CLASS_NAMES):
        carpeta = TEST_DIR / clase
        if not carpeta.is_dir():
            raise FileNotFoundError(f"No existe la carpeta de clase: {carpeta}")
        for ruta in sorted(carpeta.iterdir()):
            if ruta.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}:
                archivos.append(ruta)
                etiquetas.append(indice_clase)
    if not archivos:
        raise FileNotFoundError(f"No se encontraron imágenes en {TEST_DIR}")
    return archivos, np.asarray(etiquetas, dtype=np.int32)


def extraer_embeddings_desde_archivos(
    archivos: list[Path],
    extractor: "tf.keras.Model",
) -> np.ndarray:
    """Extrae embeddings MobileNetV2 desde una lista ordenada de archivos."""
    import tensorflow as tf
    from tensorflow.keras.preprocessing.image import img_to_array, load_img

    lotes = []
    for ruta in archivos:
        imagen = load_img(ruta, target_size=IMG_SIZE)
        arreglo = img_to_array(imagen)
        lotes.append(arreglo)
    X = np.asarray(lotes, dtype=np.float32)
    X = tf.keras.applications.mobilenet_v2.preprocess_input(X)
    embeddings = extractor.predict(X, verbose=0)
    return embeddings


def load_all_predictions():
    """Carga las predicciones de todos los modelos.
    Todas las predicciones se generan sobre la MISMA secuencia ordenada de TEST.
    """
    from extract_features import extract_single_image_features
    import tensorflow as tf

    print("🔄 Generando predicciones de todos los modelos sobre TEST...")
    archivos_test, y_test = obtener_archivos_test()
    n_test = len(y_test)
    print(f"  Total imágenes TEST: {n_test}")

    predicciones = {}
    nombres_modelos = []

    # ── Características clásicas (una sola vez para M1/M2/M3) ─────────
    X_test = np.vstack([
        np.asarray(
            extract_single_image_features(p, apply_scaler=False),
            dtype=np.float32,
        ).reshape(1, -1)
        for p in archivos_test
    ])
    if X_test.ndim != 2:
        raise ValueError(
            f"Las características clásicas deben ser 2D, "
            f"pero se obtuvo la forma {X_test.shape}."
        )
    print(f"  Características clásicas TEST: {X_test.shape}")

    # M1 — SVM (tuned)
    try:
        svm = joblib.load(M1_SVM_TUNING_PATH)
        y_pred = svm.predict(X_test)
        predicciones["M1 - SVM"] = y_pred
        nombres_modelos.append("M1 - SVM")
        print("  ✅ M1 - SVM")
    except Exception as e:
        print(f"  ⚠️  M1 - SVM: {e}")

    # M2 — Random Forest (tuned)
    try:
        rf = joblib.load(M2_RF_TUNING_PATH)
        y_pred = rf.predict(X_test)
        predicciones["M2 - Random Forest"] = y_pred
        nombres_modelos.append("M2 - Random Forest")
        print("  ✅ M2 - Random Forest")
    except Exception as e:
        print(f"  ⚠️  M2 - Random Forest: {e}")

    # M3 — KNN (tuned)
    try:
        knn = joblib.load(M3_KNN_TUNING_PATH)
        y_pred = knn.predict(X_test)
        predicciones["M3 - KNN"] = y_pred
        nombres_modelos.append("M3 - KNN")
        print("  ✅ M3 - KNN")
    except Exception as e:
        print(f"  ⚠️  M3 - KNN: {e}")

    # H1 — CNN+SVM
    try:
        from tensorflow.keras.preprocessing.image import img_to_array
        from PIL import Image
        extractor = tf.keras.models.load_model(CNN_EXTRACTOR_PATH)
        svm_cnn = joblib.load(CNN_SVM_PATH)
        X_test_cnn = np.array([
            img_to_array(Image.open(p).convert("RGB").resize(IMG_SIZE)) / 255.0
            for p in archivos_test
        ])
        feats = extractor.predict(X_test_cnn, verbose=0)
        y_pred = svm_cnn.predict(feats)
        predicciones["H1 - CNN+SVM"] = y_pred
        nombres_modelos.append("H1 - CNN+SVM")
        print("  ✅ H1 - CNN+SVM")
    except Exception as e:
        print(f"  ⚠️  H1 - CNN+SVM: {e}")

    # H2 — MobileNetV2+RF
    try:
        extractor_t = tf.keras.models.load_model(H2_EXTRACTOR_TUNING_PATH)
        rf_t = joblib.load(H2_RF_TUNING_PATH)
        X_test_h2 = extraer_embeddings_desde_archivos(archivos_test, extractor_t)
        y_pred = rf_t.predict(X_test_h2)
        predicciones["H2 - MobileNetV2+RF"] = y_pred
        nombres_modelos.append("H2 - MobileNetV2+RF")
        print("  ✅ H2 - MobileNetV2+RF")
    except Exception as e:
        print(f"  ⚠️  H2 - MobileNetV2+RF: {e}")

    # Validar que todas las predicciones tengan la misma longitud
    for nombre in nombres_modelos:
        if len(predicciones[nombre]) != n_test:
            raise ValueError(
                f"{nombre} tiene {len(predicciones[nombre])} predicciones, "
                f"pero TEST tiene {n_test} muestras."
            )

    return y_test, predicciones, nombres_modelos


# ══════════════════════════════════════════════════════════════════════════════
#  1. PRUEBA DE MCNEMAR
# ══════════════════════════════════════════════════════════════════════════════

def mcnemar_test(y_true, y_pred1, y_pred2):
    correct_1 = (y_true == y_pred1)
    correct_2 = (y_true == y_pred2)
    a = np.sum(correct_1 & correct_2)
    b = np.sum(correct_1 & ~correct_2)
    c = np.sum(~correct_1 & correct_2)
    d = np.sum(~correct_1 & ~correct_2)
    if b + c == 0:
        return {"b": 0, "c": 0, "statistic": 0.0, "p_value": 1.0, "metodo": "ninguno",
                "interpretation": "No hay diferencias entre modelos"}
    tabla = [[a, b], [c, d]]
    if b + c <= 25:
        res = sm_mcnemar(tabla, exact=True)
        metodo = "exacto"
    else:
        res = sm_mcnemar(tabla, exact=False, correction=True)
        metodo = "chi-cuadrado con corrección"
    stat = res.statistic
    p = res.pvalue
    if p < 0.001:
        interp = "Diferencia altamente significativa (p < 0.001)"
    elif p < 0.01:
        interp = "Diferencia muy significativa (p < 0.01)"
    elif p < 0.05:
        interp = "Diferencia significativa (p < 0.05)"
    else:
        interp = "No hay diferencia significativa (p >= 0.05)"
    return {"b": int(b), "c": int(c), "statistic": float(stat), "p_value": float(p),
            "metodo": metodo, "interpretation": interp}


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
        print(f"    b={res['b']}, c={res['c']}, estadístico={res['statistic']:.4f}, p={res['p_value']:.6f}, método={res['metodo']}")
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
    print(f"  p-value: {p_value:.6f}")
    print(f"  Interpretación: {interp}")

    resultado = {"estadistico_Q": float(Q), "p_value": float(p_value),
                 "interpretacion": interp, "k": k, "n": n}
    df_resultado = pd.DataFrame([resultado])
    df_resultado.to_csv(ESTADISTICA_DIR / "cochran_q_resultado.csv", index=False, float_format="%.8f")
    print(f"  ✅ Guardado: {ESTADISTICA_DIR / 'cochran_q_resultado.csv'}")
    return resultado


# ══════════════════════════════════════════════════════════════════════════════
#  3. POST-HOC: MCNEMAR CON CORRECCIÓN HOLM
# ══════════════════════════════════════════════════════════════════════════════

def posthoc_mcnemar_holm(y_true, predicciones, nombres):
    print("\n" + "=" * 60)
    print("  3. POST-HOC: McNemar con corrección Holm")
    print("=" * 60)

    mcnemar_local = mcnemar_test

    pares = list(combinations(range(len(nombres)), 2))
    p_raw_list = []
    for i, j in pares:
        n1, n2 = nombres[i], nombres[j]
        res = mcnemar_local(y_true, predicciones[n1], predicciones[n2])
        p_raw_list.append(
            {"i": i, "j": j, "n1": n1, "n2": n2,
             "p_raw": res["p_value"], "b": res["b"], "c": res["c"],
             "statistic": res["statistic"], "metodo": res["metodo"],
             "interpretation_raw": res["interpretation"]}
        )

    m = len(p_raw_list)
    sorted_pairs = sorted(enumerate(p_raw_list), key=lambda x: x[1]["p_raw"])
    sorted_indices = [idx for idx, _ in sorted_pairs]
    sorted_pvs = [pv["p_raw"] for _, pv in sorted_pairs]

    adjusted_p = []
    for k in range(m):
        current_p = sorted_pvs[k] * (m - k)
        if k == 0:
            adjusted_p.append(min(current_p, 1.0))
        else:
            adjusted_p.append(max(min(current_p, 1.0), adjusted_p[k - 1]))

    p_holm_dict = {sorted_indices[k]: adjusted_p[k] for k in range(m)}

    reject = [False] * m
    for rank, idx in enumerate(sorted_indices):
        adj_alpha = ALPHA / (m - rank)
        if p_raw_list[idx]["p_raw"] < adj_alpha:
            reject[idx] = True
        else:
            break

    resultados = []
    for idx, pv in enumerate(p_raw_list):
        pv["p_holm"] = round(p_holm_dict[idx], 4)
        pv["significativo"] = "Sí" if reject[idx] else "No"
        print(
            f"  {pv['n1']} vs {pv['n2']}: "
            f"p_raw={pv['p_raw']:.4f}, p_holm={pv['p_holm']:.4f}, "
            f"Significativo: {pv['significativo']}"
        )
        resultados.append(pv)

    df = pd.DataFrame(resultados)
    df.to_csv(ESTADISTICA_DIR / "mcnemar_holm_posthoc.csv", index=False)
    print(f"  ✅ Guardado: {ESTADISTICA_DIR / 'mcnemar_holm_posthoc.csv'}")
    return df


# ══════════════════════════════════════════════════════════════════════════════
#  4. INTERVALOS DE CONFIANZA POR BOOTSTRAP ESTRATIFICADO
# ══════════════════════════════════════════════════════════════════════════════

def bootstrap_ci_estratificado(y_true, predicciones, nombres, n_bootstrap=N_BOOTSTRAP):
    print("\n" + "=" * 60)
    print(f"  4. INTERVALOS DE CONFIANZA POR BOOTSTRAP ESTRATIFICADO ({n_bootstrap} remuestreos)")
    print("=" * 60)
    clases = np.unique(y_true)
    resultados = []
    for nombre in nombres:
        y_pred = predicciones[nombre]
        acc_boot, f1_boot, mcc_boot = [], [], []
        np.random.seed(42)
        for _ in range(n_bootstrap):
            idx_estrat = []
            for c in clases:
                mask_c = y_true == c
                idx_c = np.where(mask_c)[0]
                idx_estrat.append(
                    np.random.choice(idx_c, size=len(idx_c), replace=True)
                )
            idx = np.concatenate(idx_estrat)
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
#  5. TAMAÑO DEL EFECTO
# ══════════════════════════════════════════════════════════════════════════════

def tamano_efecto(y_true, predicciones, nombres):
    print("\n" + "=" * 60)
    print("  5. TAMAÑO DEL EFECTO")
    print("=" * 60)
    resultados = []
    for (n1, p1), (n2, p2) in combinations(zip(nombres, [predicciones[n] for n in nombres]), 2):
        acc1 = accuracy_score(y_true, p1)
        acc2 = accuracy_score(y_true, p2)
        f1_1 = f1_score(y_true, p1, average="macro", zero_division=0)
        f1_2 = f1_score(y_true, p2, average="macro", zero_division=0)
        mcc1 = matthews_corrcoef(y_true, p1)
        mcc2 = matthews_corrcoef(y_true, p2)
        diff_acc = acc1 - acc2
        diff_f1 = f1_1 - f1_2
        diff_mcc = mcc1 - mcc2
        correct_1 = (y_true == p1)
        correct_2 = (y_true == p2)
        b = np.sum(correct_1 & ~correct_2)
        c = np.sum(~correct_1 & correct_2)
        odds_ratio = (b + 0.5) / (c + 0.5)
        resultados.append({
            "modelo_1": n1, "modelo_2": n2,
            "diff_accuracy_modelo1_menos_modelo2": round(diff_acc, 4),
            "abs_diff_accuracy": round(abs(diff_acc), 4),
            "diff_f1_macro_modelo1_menos_modelo2": round(diff_f1, 4),
            "diff_mcc_modelo1_menos_modelo2": round(diff_mcc, 4),
            "odds_ratio_mcnemar_cc": round(odds_ratio, 4),
        })
        print(f"  {n1} vs {n2}: ΔAcc={diff_acc:+.4f}, ΔF1={diff_f1:+.4f}, ΔMCC={diff_mcc:+.4f}")
    df = pd.DataFrame(resultados)
    df.to_csv(ESTADISTICA_DIR / "tamano_efecto.csv", index=False)
    print(f"  ✅ Guardado: {ESTADISTICA_DIR / 'tamano_efecto.csv'}")
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
    resultado_cochran = cochran_q_test(y_true, predicciones, nombres)

    # 3. Post-hoc McNemar con corrección Holm (solo si Cochran Q es significativo)
    if resultado_cochran["p_value"] < ALPHA:
        posthoc_mcnemar_holm(y_true, predicciones, nombres)
    else:
        print(
            "\nℹ️ Cochran Q no detectó diferencias globales. "
            "El post-hoc McNemar-Holm no se ejecutará."
        )

    # 4. Bootstrap CI estratificado
    bootstrap_ci_estratificado(y_true, predicciones, nombres)

    # 5. Tamaño del efecto
    tamano_efecto(y_true, predicciones, nombres)

    print("\n" + "=" * 60)
    print("  ✅ Validación estadística completada")
    print(f"  Reportes guardados en: {ESTADISTICA_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()