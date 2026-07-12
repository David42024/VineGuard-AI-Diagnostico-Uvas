"""
seleccion_mejor_modelo.py
─────────────────────────
Selecciona automáticamente el mejor modelo según los resultados
de validación estadística y persiste sus artefactos entrenados.

No vuelve a entrenar ningún modelo.
"""

import io
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# ─────────────────────────────────────────────
# Configuración UTF-8
# ─────────────────────────────────────────────
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
elif hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(
        sys.stdout.buffer,
        encoding="utf-8",
    )


SRC_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SRC_DIR))


from mantenedor import (
    MODELS_DIR,
    MODELOS_DIR,
    ESTADISTICA_DIR,
    COMPARATIVOS_DIR,
    M1_SVM_TUNING_PATH,
    M2_RF_TUNING_PATH,
    M3_KNN_TUNING_PATH,
    H2_RF_TUNING_PATH,
    H2_EXTRACTOR_TUNING_PATH,
    CNN_EXTRACTOR_PATH,
    CNN_SVM_PATH,
)


# ─────────────────────────────────────────────
# Rutas
# ─────────────────────────────────────────────
BOOTSTRAP_PATH = (
    ESTADISTICA_DIR
    / "intervalos_confianza_bootstrap.csv"
)

POSTHOC_PATH = (
    ESTADISTICA_DIR
    / "mcnemar_holm_posthoc.csv"
)

RANKING_PATH = (
    MODELOS_DIR
    / "ranking_modelos.csv"
)

MEJOR_MODELO_PATH = (
    MODELOS_DIR
    / "mejor_modelo.txt"
)

GRAFICO_PATH = (
    COMPARATIVOS_DIR
    / "comparacion_metricas_modelos.png"
)

MODELO_FINAL_DIR = (
    MODELS_DIR
    / "modelo_final"
)

MANIFIESTO_FINAL_PATH = (
    MODELO_FINAL_DIR
    / "modelo_final.json"
)


MODELOS_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

COMPARATIVOS_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

MODELO_FINAL_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ─────────────────────────────────────────────
# Artefactos disponibles por modelo
# ─────────────────────────────────────────────
ARTEFACTOS_MODELOS = {
    "M1 - SVM": [
        {
            "tipo": "modelo",
            "origen": M1_SVM_TUNING_PATH,
            "destino": (
                MODELO_FINAL_DIR
                / "modelo_m1_svm.pkl"
            ),
        },
    ],

    "M2 - Random Forest": [
        {
            "tipo": "modelo",
            "origen": M2_RF_TUNING_PATH,
            "destino": (
                MODELO_FINAL_DIR
                / "modelo_m2_random_forest.pkl"
            ),
        },
    ],

    "M3 - KNN": [
        {
            "tipo": "modelo",
            "origen": M3_KNN_TUNING_PATH,
            "destino": (
                MODELO_FINAL_DIR
                / "modelo_m3_knn.pkl"
            ),
        },
    ],

    "H1 - CNN+SVM": [
        {
            "tipo": "extractor",
            "origen": CNN_EXTRACTOR_PATH,
            "destino": (
                MODELO_FINAL_DIR
                / "h1_cnn_feature_extractor.h5"
            ),
        },
        {
            "tipo": "clasificador",
            "origen": CNN_SVM_PATH,
            "destino": (
                MODELO_FINAL_DIR
                / "h1_svm_classifier.pkl"
            ),
        },
    ],

    "H2 - MobileNetV2+RF": [
        {
            "tipo": "extractor",
            "origen": H2_EXTRACTOR_TUNING_PATH,
            "destino": (
                MODELO_FINAL_DIR
                / "h2_mobilenetv2_extractor.keras"
            ),
        },
        {
            "tipo": "clasificador",
            "origen": H2_RF_TUNING_PATH,
            "destino": (
                MODELO_FINAL_DIR
                / "h2_random_forest.pkl"
            ),
        },
    ],
}


def cargar_metricas() -> pd.DataFrame:
    """
    Carga las métricas obtenidas por bootstrap
    sobre el conjunto TEST.
    """
    if not BOOTSTRAP_PATH.is_file():
        raise FileNotFoundError(
            "No se encontró el archivo de métricas: "
            f"{BOOTSTRAP_PATH}"
        )

    df = pd.read_csv(
        BOOTSTRAP_PATH
    )

    columnas_requeridas = {
        "modelo",
        "acc_media",
        "f1_media",
        "mcc_media",
    }

    faltantes = (
        columnas_requeridas
        - set(df.columns)
    )

    if faltantes:
        raise ValueError(
            "El archivo de bootstrap no contiene "
            "las columnas requeridas: "
            f"{sorted(faltantes)}"
        )

    df = df.rename(
        columns={
            "acc_media": "accuracy",
            "f1_media": "f1_macro",
            "mcc_media": "mcc",
        }
    ).copy()

    columnas_numericas = [
        "accuracy",
        "f1_macro",
        "mcc",
    ]

    for columna in columnas_numericas:
        df[columna] = pd.to_numeric(
            df[columna],
            errors="coerce",
        )

    df = df.dropna(
        subset=[
            "modelo",
            "accuracy",
            "f1_macro",
            "mcc",
        ]
    ).copy()

    if df.empty:
        raise ValueError(
            "No existen modelos con métricas válidas."
        )

    return df


def crear_ranking(
    df_metricas: pd.DataFrame,
) -> pd.DataFrame:
    """
    Ordena los modelos por:
    1. MCC
    2. F1-macro
    3. Accuracy
    """
    df = df_metricas.sort_values(
        by=[
            "mcc",
            "f1_macro",
            "accuracy",
        ],
        ascending=[
            False,
            False,
            False,
        ],
    ).reset_index(
        drop=True
    )

    df.insert(
        0,
        "ranking",
        range(
            1,
            len(df) + 1,
        ),
    )

    return df


def contar_comparaciones_significativas(
    modelo_ganador: str,
) -> int:
    """
    Cuenta las comparaciones significativas en las que
    participó el modelo ganador.
    """
    if not POSTHOC_PATH.is_file():
        return 0

    df = pd.read_csv(
        POSTHOC_PATH
    )

    columnas_requeridas = {
        "n1",
        "n2",
        "significativo",
    }

    if not columnas_requeridas.issubset(
        df.columns
    ):
        return 0

    comparaciones = df[
        (
            df["n1"]
            == modelo_ganador
        )
        | (
            df["n2"]
            == modelo_ganador
        )
    ].copy()

    valores_significativos = {
        "sí",
        "si",
        "true",
        "1",
        "yes",
    }

    mascara = (
        comparaciones["significativo"]
        .astype(str)
        .str.strip()
        .str.lower()
        .isin(valores_significativos)
    )

    return int(
        mascara.sum()
    )


def limpiar_modelo_final() -> None:
    """
    Elimina artefactos anteriores de la carpeta final,
    sin borrar la carpeta.
    """
    MODELO_FINAL_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    for ruta in MODELO_FINAL_DIR.iterdir():
        if ruta.is_file():
            ruta.unlink()
        elif ruta.is_dir():
            shutil.rmtree(
                ruta
            )


def persistir_modelo_ganador(
    modelo_ganador: str,
    ganador: pd.Series,
    comparaciones_significativas: int,
) -> None:
    """
    Copia los artefactos ya entrenados del modelo ganador
    a una carpeta final estable.

    No realiza entrenamiento.
    """
    if modelo_ganador not in ARTEFACTOS_MODELOS:
        raise ValueError(
            "No existe una configuración de artefactos "
            f"para el modelo: {modelo_ganador}"
        )

    artefactos = ARTEFACTOS_MODELOS[
        modelo_ganador
    ]

    faltantes = [
        artefacto["origen"]
        for artefacto in artefactos
        if not artefacto["origen"].is_file()
    ]

    if faltantes:
        texto_faltantes = "\n".join(
            f"  - {ruta}"
            for ruta in faltantes
        )

        raise FileNotFoundError(
            "No se pudieron persistir los artefactos "
            "del modelo ganador porque faltan:\n"
            f"{texto_faltantes}"
        )

    limpiar_modelo_final()

    artefactos_guardados = []

    for artefacto in artefactos:
        origen = artefacto["origen"]
        destino = artefacto["destino"]

        destino.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        shutil.copy2(
            origen,
            destino,
        )

        artefactos_guardados.append({
            "tipo": artefacto["tipo"],
            "ruta": str(
                destino.resolve()
            ),
            "nombre_archivo": destino.name,
        })

        print(
            f"  💾 {artefacto['tipo'].capitalize()}: "
            f"{destino}"
        )

    manifiesto = {
        "modelo_ganador": modelo_ganador,
        "fecha_seleccion": datetime.now().isoformat(
            timespec="seconds"
        ),
        "criterio_seleccion": [
            "Mayor MCC",
            "Mayor F1-macro en caso de empate",
            "Mayor accuracy en caso de empate",
        ],
        "metricas_test": {
            "accuracy": float(
                ganador["accuracy"]
            ),
            "f1_macro": float(
                ganador["f1_macro"]
            ),
            "mcc": float(
                ganador["mcc"]
            ),
        },
        "comparaciones_significativas_holm": int(
            comparaciones_significativas
        ),
        "requiere_reentrenamiento": False,
        "artefactos": artefactos_guardados,
    }

    MANIFIESTO_FINAL_PATH.write_text(
        json.dumps(
            manifiesto,
            ensure_ascii=False,
            indent=4,
        ),
        encoding="utf-8",
    )

    print(
        f"  💾 Manifiesto: "
        f"{MANIFIESTO_FINAL_PATH}"
    )


def guardar_grafico(
    df_ranking: pd.DataFrame,
) -> None:
    """
    Genera un gráfico comparativo sencillo.
    """
    modelos = df_ranking[
        "modelo"
    ].tolist()

    posiciones = np.arange(
        len(modelos)
    )

    ancho = 0.25

    figura, eje = plt.subplots(
        figsize=(12, 6)
    )

    eje.bar(
        posiciones - ancho,
        df_ranking["accuracy"],
        width=ancho,
        label="Accuracy",
    )

    eje.bar(
        posiciones,
        df_ranking["f1_macro"],
        width=ancho,
        label="F1-macro",
    )

    eje.bar(
        posiciones + ancho,
        df_ranking["mcc"],
        width=ancho,
        label="MCC",
    )

    eje.set_title(
        "Comparación final de modelos"
    )

    eje.set_ylabel(
        "Valor de la métrica"
    )

    valor_minimo = min(
        df_ranking["accuracy"].min(),
        df_ranking["f1_macro"].min(),
        df_ranking["mcc"].min(),
    )

    limite_inferior = max(
        0,
        valor_minimo - 0.03,
    )

    eje.set_ylim(
        limite_inferior,
        1.01,
    )

    eje.set_xticks(
        posiciones
    )

    eje.set_xticklabels(
        modelos,
        rotation=15,
        ha="right",
    )

    eje.legend()

    figura.tight_layout()

    figura.savefig(
        GRAFICO_PATH,
        dpi=180,
        bbox_inches="tight",
    )

    plt.close(
        figura
    )


def guardar_resultados(
    df_ranking: pd.DataFrame,
    ganador: pd.Series,
    comparaciones_significativas: int,
) -> None:
    """
    Guarda el ranking y la justificación del ganador.
    """
    columnas = [
        "ranking",
        "modelo",
        "accuracy",
        "f1_macro",
        "mcc",
        "acc_ci_inf",
        "acc_ci_sup",
        "f1_ci_inf",
        "f1_ci_sup",
        "mcc_ci_inf",
        "mcc_ci_sup",
    ]

    columnas_existentes = [
        columna
        for columna in columnas
        if columna in df_ranking.columns
    ]

    df_ranking[
        columnas_existentes
    ].to_csv(
        RANKING_PATH,
        index=False,
        float_format="%.6f",
    )

    modelo_ganador = str(
        ganador["modelo"]
    )

    justificacion = (
        f"Mejor modelo seleccionado: {modelo_ganador}\n\n"
        f"Accuracy: {ganador['accuracy']:.4f}\n"
        f"F1-macro: {ganador['f1_macro']:.4f}\n"
        f"MCC: {ganador['mcc']:.4f}\n\n"
        "Criterio de selección:\n"
        "- Mayor MCC en el conjunto TEST.\n"
        "- F1-macro utilizado como segundo criterio.\n"
        "- Accuracy utilizada como tercer criterio.\n\n"
        "Respaldo estadístico:\n"
        f"- Comparaciones significativas con corrección de Holm: "
        f"{comparaciones_significativas}.\n\n"
        "El modelo fue persistido para realizar inferencias "
        "sin volver a entrenarlo.\n"
    )

    MEJOR_MODELO_PATH.write_text(
        justificacion,
        encoding="utf-8",
    )


def main() -> None:
    print("=" * 65)
    print("  SELECCIÓN FINAL DEL MEJOR MODELO — VineGuard AI")
    print("=" * 65)

    df_metricas = cargar_metricas()

    df_ranking = crear_ranking(
        df_metricas
    )

    ganador = df_ranking.iloc[0]

    modelo_ganador = str(
        ganador["modelo"]
    )

    comparaciones_significativas = (
        contar_comparaciones_significativas(
            modelo_ganador
        )
    )

    guardar_resultados(
        df_ranking,
        ganador,
        comparaciones_significativas,
    )

    guardar_grafico(
        df_ranking
    )

    print("\n  RANKING FINAL")
    print("-" * 72)

    print(
        df_ranking[
            [
                "ranking",
                "modelo",
                "accuracy",
                "f1_macro",
                "mcc",
            ]
        ].to_string(
            index=False
        )
    )

    print("\n" + "=" * 65)
    print("  🏆 MEJOR MODELO SELECCIONADO")
    print("=" * 65)

    print(
        f"  Modelo: {modelo_ganador}"
    )

    print(
        f"  Accuracy: "
        f"{ganador['accuracy']:.4f}"
    )

    print(
        f"  F1-macro: "
        f"{ganador['f1_macro']:.4f}"
    )

    print(
        f"  MCC: "
        f"{ganador['mcc']:.4f}"
    )

    print(
        f"  Comparaciones significativas: "
        f"{comparaciones_significativas}"
    )

    print(
        "\n  Persistiendo artefactos "
        "del modelo ganador..."
    )

    persistir_modelo_ganador(
        modelo_ganador,
        ganador,
        comparaciones_significativas,
    )

    print(
        f"\n  ✅ Ranking: "
        f"{RANKING_PATH}"
    )

    print(
        f"  ✅ Resultado final: "
        f"{MEJOR_MODELO_PATH}"
    )

    print(
        f"  ✅ Gráfico: "
        f"{GRAFICO_PATH}"
    )

    print(
        f"  ✅ Modelo persistido en: "
        f"{MODELO_FINAL_DIR}"
    )

    print(
        "\n✅ Selección y persistencia completadas."
    )


if __name__ == "__main__":
    main()