"""
predecir_imagen.py
-----------------
Predicción en producción para VineGuard AI.
Carga modelos bajo demanda y permite predicción individual o de todos los
modelos disponibles.
"""

import sys
from pathlib import Path
from typing import Any

import numpy as np
import joblib
from PIL import Image, UnidentifiedImageError

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
elif hasattr(sys.stdout, "buffer"):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

SRC_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SRC_DIR))

from mantenedor import (
    CLASS_NAMES,
    IMG_SIZE,
    IMAGE_EXTENSIONS,
    M1_SVM_TUNING_PATH,
    M2_RF_TUNING_PATH,
    M3_KNN_TUNING_PATH,
    H2_RF_TUNING_PATH,
    H2_EXTRACTOR_TUNING_PATH,
    CNN_EXTRACTOR_PATH,
    CNN_SVM_PATH,
)
from extract_features import extract_single_image_features
from preprocesamiento_h2 import extraer_embedding_una_imagen

_modelos: dict[str, Any] = {}
_extractores: dict[str, Any] = {}


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------

def validar_imagen(ruta: str | Path) -> Path:
    r = Path(ruta)
    if not r.exists():
        raise FileNotFoundError(f"La ruta no existe: {r}")
    if not r.is_file():
        raise ValueError(f"La ruta no es un archivo: {r}")
    if r.suffix.lower() not in IMAGE_EXTENSIONS:
        raise ValueError(
            f"Extensión no soportada: {r.suffix}. "
            f"Permitidas: {', '.join(sorted(IMAGE_EXTENSIONS))}"
        )
    try:
        with Image.open(r) as imagen:
            imagen.verify()
    except (UnidentifiedImageError, OSError) as exc:
        raise ValueError(
            f"El archivo no es una imagen válida o está dañado: {r}"
        ) from exc
    return r


def convertir_prediccion_a_clase(prediccion: Any) -> tuple[int | None, str]:
    if isinstance(prediccion, (np.integer, int)):
        idx = int(prediccion)
        if 0 <= idx < len(CLASS_NAMES):
            return idx, CLASS_NAMES[idx]
        raise ValueError(
            f"Índice de clase {idx} fuera de rango (0-{len(CLASS_NAMES)-1})"
        )
    if isinstance(prediccion, str):
        if prediccion in CLASS_NAMES:
            return CLASS_NAMES.index(prediccion), prediccion
        raise ValueError(f"Nombre de clase '{prediccion}' no reconocido")
    raise ValueError(f"Tipo de predicción no soportado: {type(prediccion)}")


def ordenar_probabilidades(
    modelo_obj: Any,
    probabilidades: np.ndarray,
) -> list[float]:
    if not hasattr(modelo_obj, "classes_"):
        raise AttributeError(
            "El modelo no contiene el atributo 'classes_'; "
            "no se puede determinar el orden de las probabilidades."
        )

    clases_modelo = np.asarray(modelo_obj.classes_)
    probs = np.asarray(probabilidades, dtype=np.float64).ravel()

    if probs.size != clases_modelo.size:
        raise ValueError(
            f"Se obtuvieron {probs.size} probabilidades, pero el modelo "
            f"contiene {clases_modelo.size} clases."
        )

    resultado = np.zeros(len(CLASS_NAMES), dtype=np.float64)
    indices_asignados: set[int] = set()

    for posicion, clase in enumerate(clases_modelo):
        if isinstance(clase, (int, np.integer)):
            indice = int(clase)
        elif isinstance(clase, str):
            if clase not in CLASS_NAMES:
                raise ValueError(
                    f"El modelo contiene una clase no reconocida: {clase!r}"
                )
            indice = CLASS_NAMES.index(clase)
        else:
            raise ValueError(
                f"Tipo de clase no soportado en classes_: {type(clase)}"
            )

        if not 0 <= indice < len(CLASS_NAMES):
            raise ValueError(
                f"Índice de clase fuera de rango: {indice}"
            )

        if indice in indices_asignados:
            raise ValueError(
                f"El modelo contiene una clase duplicada: {clase!r}"
            )

        resultado[indice] = float(probs[posicion])
        indices_asignados.add(indice)

    return resultado.tolist()


def _obtener_probabilidades(
    modelo_obj: Any,
    X: np.ndarray,
) -> tuple[list[float] | None, str | None]:
    if hasattr(modelo_obj, "predict_proba"):
        raw = np.asarray(
            modelo_obj.predict_proba(X),
            dtype=np.float64,
        )
        if raw.ndim != 2 or raw.shape[0] != 1:
            raise ValueError(
                f"Forma inesperada de predict_proba: {raw.shape}"
            )
        probabilidades = ordenar_probabilidades(modelo_obj, raw[0])
        return probabilidades, "predict_proba"

    if hasattr(modelo_obj, "decision_function"):
        scores = np.asarray(
            modelo_obj.decision_function(X),
            dtype=np.float64,
        )
        if scores.ndim == 2:
            scores = scores[0]
        scores = scores.ravel()

        if scores.size == 1:
            return None, None

        exp_scores = np.exp(scores - np.max(scores))
        probabilidades = exp_scores / exp_scores.sum()

        probabilidades_ordenadas = ordenar_probabilidades(
            modelo_obj,
            probabilidades,
        )
        return probabilidades_ordenadas, "softmax_aproximado"

    return None, None


# ---------------------------------------------------------------------------
# Carga bajo demanda de modelos / extractores
# ---------------------------------------------------------------------------

def _cargar_modelo_m1() -> None:
    if "M1" not in _modelos:
        print(f"  Cargando M1 desde {M1_SVM_TUNING_PATH.name}...")
        _modelos["M1"] = joblib.load(M1_SVM_TUNING_PATH)
        print("  ✅ M1 cargado")


def _cargar_modelo_m2() -> None:
    if "M2" not in _modelos:
        print(f"  Cargando M2 desde {M2_RF_TUNING_PATH.name}...")
        _modelos["M2"] = joblib.load(M2_RF_TUNING_PATH)
        print("  ✅ M2 cargado")


def _cargar_modelo_m3() -> None:
    if "M3" not in _modelos:
        print(f"  Cargando M3 desde {M3_KNN_TUNING_PATH.name}...")
        _modelos["M3"] = joblib.load(M3_KNN_TUNING_PATH)
        print("  ✅ M3 cargado")


def _cargar_modelo_h1() -> None:
    import tensorflow as tf
    tf.get_logger().setLevel("ERROR")
    if "H1_extractor" not in _extractores:
        print(f"  Cargando extractor H1 desde {CNN_EXTRACTOR_PATH.name}...")
        _extractores["H1_extractor"] = tf.keras.models.load_model(
            CNN_EXTRACTOR_PATH, compile=False,
        )
        print("  ✅ Extractor H1 cargado")
    if "H1_svm" not in _modelos:
        print(f"  Cargando SVM H1 desde {CNN_SVM_PATH.name}...")
        _modelos["H1_svm"] = joblib.load(CNN_SVM_PATH)
        print("  ✅ SVM H1 cargado")


def _cargar_modelo_h2() -> None:
    import tensorflow as tf
    tf.get_logger().setLevel("ERROR")
    if "H2_extractor" not in _extractores:
        print(f"  Cargando extractor H2 desde {H2_EXTRACTOR_TUNING_PATH.name}...")
        _extractores["H2_extractor"] = tf.keras.models.load_model(
            H2_EXTRACTOR_TUNING_PATH, compile=False,
        )
        print("  ✅ Extractor H2 cargado")
    if "H2" not in _modelos:
        print(f"  Cargando H2 desde {H2_RF_TUNING_PATH.name}...")
        _modelos["H2"] = joblib.load(H2_RF_TUNING_PATH)
        print("  ✅ H2 cargado")


def cargar_modelo(nombre_modelo: str) -> None:
    """Carga únicamente el modelo solicitado y sus extractores."""
    mapa = {
        "M1": _cargar_modelo_m1,
        "M2": _cargar_modelo_m2,
        "M3": _cargar_modelo_m3,
    }
    if nombre_modelo in mapa:
        mapa[nombre_modelo]()
        return
    if nombre_modelo == "H1":
        _cargar_modelo_h1()
        return
    if nombre_modelo == "H2":
        _cargar_modelo_h2()
        return
    raise ValueError(f"Modelo '{nombre_modelo}' no válido")


# ---------------------------------------------------------------------------
# Predicción individual
# ---------------------------------------------------------------------------

def predecir(ruta_imagen: str | Path, modelo: str) -> dict[str, Any]:
    ruta = validar_imagen(ruta_imagen)
    return _predecir_con(ruta, modelo)


# ---------------------------------------------------------------------------
# Predicción con todos los modelos disponibles
# ---------------------------------------------------------------------------

def predecir_todos(ruta_imagen: str | Path) -> dict[str, dict[str, Any]]:
    ruta = validar_imagen(ruta_imagen)
    modelos = ["M1", "M2", "M3", "H1", "H2"]
    resultados: dict[str, dict[str, Any]] = {}
    hubo_alguno = False

    # Extraer características clásicas una sola vez para M1/M2/M3
    X_clasico: np.ndarray | None = None
    error_features_clasicas: Exception | None = None
    try:
        features_clasicas = extract_single_image_features(ruta, apply_scaler=False)
        X_clasico = np.asarray(features_clasicas, dtype=np.float32).reshape(1, -1)
    except Exception as exc:
        error_features_clasicas = exc

    for nombre in modelos:
        if nombre in {"M1", "M2", "M3"} and error_features_clasicas is not None:
            resultados[nombre] = {
                "modelo": nombre,
                "disponible": False,
                "error": (
                    "No se pudieron extraer las características clásicas: "
                    f"{error_features_clasicas}"
                ),
            }
            continue

        ctx: dict[str, Any] = {}
        if nombre in {"M1", "M2", "M3"} and X_clasico is not None:
            ctx["X_clasico"] = X_clasico

        try:
            resultado = _predecir_con(ruta, nombre, ctx)
            resultados[nombre] = resultado
            hubo_alguno = True
        except FileNotFoundError as e:
            resultados[nombre] = {
                "modelo": nombre,
                "disponible": False,
                "error": f"No se encontraron los archivos requeridos: {e}",
            }
        except Exception as e:
            resultados[nombre] = {
                "modelo": nombre,
                "disponible": False,
                "error": str(e),
            }

    if not hubo_alguno:
        raise RuntimeError(
            "Ningún modelo está disponible. Revisa los archivos de modelo en las "
            "rutas esperadas."
        )
    return resultados


def _predecir_con(
    ruta: Path,
    modelo: str,
    ctx: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Realiza la predicción interna con una ruta previamente validada."""
    ctx = ctx or {}
    cargar_modelo(modelo)

    if modelo in {"M1", "M2", "M3"}:
        X = ctx.get("X_clasico")
        if X is None:
            features = extract_single_image_features(ruta, apply_scaler=False)
            X = np.asarray(features, dtype=np.float32).reshape(1, -1)
        obj = _modelos[modelo]
        pred = obj.predict(X)[0]
        probs, metodo = _obtener_probabilidades(obj, X)

    elif modelo == "H1":
        from PIL import Image as _PIL
        from tensorflow.keras.preprocessing.image import img_to_array
        extractor, svm = _extractores["H1_extractor"], _modelos["H1_svm"]
        with _PIL.open(ruta) as imagen:
            imagen_rgb = imagen.convert("RGB").resize(IMG_SIZE)
            arr = img_to_array(imagen_rgb) / 255.0
        feats = extractor.predict(arr[np.newaxis, ...], verbose=0)
        feats = np.asarray(feats, dtype=np.float32).reshape(1, -1)
        pred = svm.predict(feats)[0]
        probs, metodo = _obtener_probabilidades(svm, feats)

    elif modelo == "H2":
        extractor, rf = _extractores["H2_extractor"], _modelos["H2"]
        embedding = extraer_embedding_una_imagen(ruta, extractor)
        X = np.asarray(embedding, dtype=np.float32).reshape(1, -1)
        pred = rf.predict(X)[0]
        probs, metodo = _obtener_probabilidades(rf, X)

    else:
        raise ValueError(
            f"Modelo '{modelo}' no válido. "
            "Opciones: M1, M2, M3, H1, H2"
        )

    idx, clase = convertir_prediccion_a_clase(pred)

    return {
        "modelo": modelo,
        "disponible": True,
        "indice_clase": idx,
        "clase_predicha": clase,
        "probabilidades": probs,
        "orden_clases": list(CLASS_NAMES),
        "metodo_probabilidades": metodo,
        "probabilidades_calibradas": False,
    }


# ---------------------------------------------------------------------------
# Interfaz de consola
# ---------------------------------------------------------------------------

def _mostrar_individual(resultado: dict[str, Any]) -> None:
    print(f"\nPredicción con {resultado['modelo']}")
    if not resultado.get("disponible", False):
        print(f"  No disponible: {resultado.get('error', 'error desconocido')}")
        return
    print(f"  Clase predicha: {resultado['clase_predicha']}")
    probs = resultado.get("probabilidades")
    if probs is not None:
        print("\n  Probabilidades por clase:")
        for nombre, prob in zip(resultado["orden_clases"], probs):
            print(f"    {nombre}: {prob:.4f}")
    print(f"\n  Método de probabilidades: {resultado.get('metodo_probabilidades', 'N/A')}")
    print(f"  Probabilidades calibradas: {'Sí' if resultado.get('probabilidades_calibradas', False) else 'No'}")


def _mostrar_todos(resultados: dict[str, dict[str, Any]]) -> None:
    print("\nResultados de predicción")
    for nombre, res in resultados.items():
        print(f"\n{nombre}")
        if res.get("disponible", False):
            print(f"  Clase predicha: {res['clase_predicha']}")
            probs = res.get("probabilidades")
            indice = res.get("indice_clase")
            if probs is not None and indice is not None:
                probabilidad_predicha = probs[indice]
                print(
                    f"  Probabilidad de la clase predicha: "
                    f"{probabilidad_predicha:.4f}"
                )
        else:
            print(f"  No disponible: {res.get('error', 'error desconocido')}")


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(
        description="Realiza una predicción sobre una imagen con VineGuard AI.",
    )
    parser.add_argument("ruta_imagen", type=str, help="Ruta a la imagen a predecir")
    grupo = parser.add_mutually_exclusive_group()
    grupo.add_argument(
        "--modelo",
        type=str,
        default=None,
        choices=["M1", "M2", "M3", "H1", "H2"],
        help="Modelo a usar (por defecto: M1)",
    )
    grupo.add_argument(
        "--todos",
        action="store_true",
        help="Ejecutar predicción con todos los modelos disponibles",
    )
    args = parser.parse_args()

    try:
        if args.todos:
            resultados = predecir_todos(args.ruta_imagen)
            _mostrar_todos(resultados)
        else:
            modelo = args.modelo or "M1"
            resultado = predecir(args.ruta_imagen, modelo)
            _mostrar_individual(resultado)
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
