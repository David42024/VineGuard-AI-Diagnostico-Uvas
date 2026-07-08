"""
optimizacion_hiperparametros.py
Búsqueda de hiperparámetros para los modelos M1, M2, M3 y H2.
Usa GridSearchCV con validación cruzada (StratifiedKFold, 3 folds).
"""

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import GridSearchCV, StratifiedKFold
from sklearn.svm import SVC
from sklearn.ensemble import RandomForestClassifier
from sklearn.neighbors import KNeighborsClassifier

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

MODELOS_DIR.mkdir(parents=True, exist_ok=True)


def grid_search(modelo, param_grid, nombre, X, y, cv=3):
    print(f"\n🔍 Buscando hiperparámetros para {nombre}...")
    skf = StratifiedKFold(n_splits=cv, shuffle=True, random_state=SEED)
    gs = GridSearchCV(
        modelo, param_grid, cv=skf, scoring="accuracy",
        n_jobs=-1, verbose=1, return_train_score=True,
    )
    gs.fit(X, y)
    print(f"\n  Mejores parámetros: {gs.best_params_}")
    print(f"  Mejor accuracy (CV): {gs.best_score_:.4f}")
    return gs


def main():
    print("=" * 60)
    print("  OPTIMIZACIÓN DE HIPERPARÁMETROS — VineGuard AI")
    print("=" * 60)

    print("\n🔄 Cargando características...")
    X_train, y_train, X_test, y_test = load_features(fit_scaler=False)
    X = np.concatenate([X_train, X_test], axis=0)
    y = np.concatenate([y_train, y_test], axis=0)
    print(f"  Total muestras: {len(y)}, features: {X.shape[1]}")

    mejores_params = []
    resultados_grid = []

    # ── M1: SVM ──────────────────────────────────────────────────────────────
    svm = SVC(probability=True, class_weight="balanced", random_state=SEED)
    param_svm = {
        "kernel": ["linear", "rbf"],
        "C": [0.1, 1, 10, 100],
        "gamma": ["scale", "auto"],
    }
    gs_svm = grid_search(svm, param_svm, "M1 - SVM", X, y)
    mejores_params.append({"modelo": "M1 - SVM", "mejores_parametros": str(gs_svm.best_params_),
                           "mejor_score_cv": round(gs_svm.best_score_, 4)})
    for params, mean_score, std_score in zip(gs_svm.cv_results_["params"],
                                              gs_svm.cv_results_["mean_test_score"],
                                              gs_svm.cv_results_["std_test_score"]):
        resultados_grid.append({"modelo": "M1 - SVM", "parametros": str(params),
                                "mean_test_score": round(mean_score, 4), "std_test_score": round(std_score, 4)})

    # ── M2: Random Forest ────────────────────────────────────────────────────
    rf = RandomForestClassifier(class_weight="balanced", random_state=SEED, n_jobs=-1)
    param_rf = {
        "n_estimators": [100, 200, 300],
        "max_depth": [None, 10, 20, 30],
        "min_samples_split": [2, 5, 10],
        "min_samples_leaf": [1, 2, 4],
    }
    gs_rf = grid_search(rf, param_rf, "M2 - Random Forest", X, y)
    mejores_params.append({"modelo": "M2 - Random Forest", "mejores_parametros": str(gs_rf.best_params_),
                           "mejor_score_cv": round(gs_rf.best_score_, 4)})
    for params, mean_score, std_score in zip(gs_rf.cv_results_["params"],
                                              gs_rf.cv_results_["mean_test_score"],
                                              gs_rf.cv_results_["std_test_score"]):
        resultados_grid.append({"modelo": "M2 - Random Forest", "parametros": str(params),
                                "mean_test_score": round(mean_score, 4), "std_test_score": round(std_score, 4)})

    # ── M3: KNN ──────────────────────────────────────────────────────────────
    knn = KNeighborsClassifier(n_jobs=-1)
    param_knn = {
        "n_neighbors": [3, 5, 7, 9],
        "weights": ["uniform", "distance"],
        "metric": ["euclidean", "manhattan"],
    }
    gs_knn = grid_search(knn, param_knn, "M3 - KNN", X, y)
    mejores_params.append({"modelo": "M3 - KNN", "mejores_parametros": str(gs_knn.best_params_),
                           "mejor_score_cv": round(gs_knn.best_score_, 4)})
    for params, mean_score, std_score in zip(gs_knn.cv_results_["params"],
                                              gs_knn.cv_results_["mean_test_score"],
                                              gs_knn.cv_results_["std_test_score"]):
        resultados_grid.append({"modelo": "M3 - KNN", "parametros": str(params),
                                "mean_test_score": round(mean_score, 4), "std_test_score": round(std_score, 4)})

    # ── H2: Transfer Learning + RF ──────────────────────────────────────────
    try:
        print("\n🔍 Buscando hiperparámetros para H2 - Transfer + RF...")
        print("  (Requiere embeddings MobileNetV2; usando features existentes como aproximación)")
        rf_h2 = RandomForestClassifier(class_weight="balanced", random_state=SEED, n_jobs=-1)
        param_rf_h2 = {
            "n_estimators": [100, 200, 300],
            "max_depth": [None, 10, 20],
            "min_samples_split": [2, 5],
            "min_samples_leaf": [1, 2],
        }
        gs_h2 = grid_search(rf_h2, param_rf_h2, "H2 - Transfer + RF", X, y)
        mejores_params.append({"modelo": "H2 - Transfer + RF", "mejores_parametros": str(gs_h2.best_params_),
                               "mejor_score_cv": round(gs_h2.best_score_, 4)})
        for params, mean_score, std_score in zip(gs_h2.cv_results_["params"],
                                                  gs_h2.cv_results_["mean_test_score"],
                                                  gs_h2.cv_results_["std_test_score"]):
            resultados_grid.append({"modelo": "H2 - Transfer + RF", "parametros": str(params),
                                    "mean_test_score": round(mean_score, 4), "std_test_score": round(std_score, 4)})
    except Exception as e:
        print(f"  ⚠️  Error en H2: {e}")

    # ── Guardar resultados ──────────────────────────────────────────────────
    df_mejores = pd.DataFrame(mejores_params)
    df_mejores.to_csv(MODELOS_DIR / "mejores_hiperparametros.csv", index=False)
    print(f"\n✅ Mejores hiperparámetros guardados en: {MODELOS_DIR / 'mejores_hiperparametros.csv'}")

    df_grid = pd.DataFrame(resultados_grid)
    df_grid.to_csv(MODELOS_DIR / "resultados_gridsearch.csv", index=False)
    print(f"✅ Resultados GridSearch guardados en: {MODELOS_DIR / 'resultados_gridsearch.csv'}")

    print("\n" + "=" * 60)
    print("  MEJORES HIPERPARÁMETROS ENCONTRADOS")
    print("=" * 60)
    print(df_mejores.to_string(index=False))
    print("\n✅ Optimización completada.")


if __name__ == "__main__":
    main()
