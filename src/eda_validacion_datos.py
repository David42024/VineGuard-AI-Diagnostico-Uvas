"""
eda_validacion_datos.py
────────────────────────────────────────────────────────────────────────────
Análisis Exploratorio de Datos (EDA) y Validación del Dataset
VineGuard AI — Diagnóstico de Enfermedades en Hojas de Uva

Analiza:
  • dataset_original/
  • dataset/train/
  • dataset/test/

Genera reportes en: reports/eda/

Uso:
  python src/eda_validacion_datos.py
"""

import sys
import csv
import hashlib
import random
import warnings
from pathlib import Path
from collections import defaultdict, Counter
from datetime import datetime

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")                          # backend sin GUI (compatible con servidores)
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from PIL import Image

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
elif hasattr(sys.stdout, 'buffer'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

warnings.filterwarnings("ignore", category=UserWarning)

# ─── Importar configuración del proyecto ────────────────────────────────────
sys.path.insert(0, str(Path(__file__).resolve().parent))
from mantenedor import (
    DATASET_ORIGINAL_DIR,
    DATASET_DIR,
    TRAIN_DIR,
    TEST_DIR,
    CLASS_NAMES,
    CLASS_FOLDER_MAP,
    IMG_SIZE,
    SEED,
    TARGET_TRAIN_SAMPLES_PER_CLASS,
)

# ─── Constantes ──────────────────────────────────────────────────────────────
REPORTS_DIR = Path(__file__).resolve().parent.parent / "reports" / "eda"
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
BALANCE_RATIO_THRESHOLD = 1.5

SECTION_WIDTH = 62


# ══════════════════════════════════════════════════════════════════════════════
#  UTILIDADES GENERALES
# ══════════════════════════════════════════════════════════════════════════════

def _titulo(texto: str, char: str = "═") -> None:
    print("\n" + char * SECTION_WIDTH)
    print(f"  {texto}")
    print(char * SECTION_WIDTH)


def _subtitulo(texto: str) -> None:
    print(f"\n  ── {texto} {'─' * max(0, SECTION_WIDTH - len(texto) - 6)}")


def _listar_imagenes(directorio: Path) -> list[Path]:
    """Devuelve lista de rutas de imagen válidas dentro de un directorio."""
    if not directorio.exists():
        return []
    return [
        p for p in directorio.rglob("*")
        if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS
    ]


def _listar_todas(directorio: Path) -> list[Path]:
    """Devuelve TODOS los archivos dentro de un directorio (incluyendo no imágenes)."""
    if not directorio.exists():
        return []
    return [p for p in directorio.rglob("*") if p.is_file()]


def _hash_archivo(ruta: Path) -> str:
    """Calcula hash SHA-256 del contenido del archivo."""
    h = hashlib.sha256()
    try:
        with open(ruta, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return ""


def _guardar_csv(ruta: Path, filas: list[dict], campos: list[str]) -> None:
    """Guarda una lista de dicts como CSV."""
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with open(ruta, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=campos)
        writer.writeheader()
        writer.writerows(filas)


# ══════════════════════════════════════════════════════════════════════════════
#  1. VALIDACIÓN DE ESTRUCTURA DE CARPETAS
# ══════════════════════════════════════════════════════════════════════════════

def validar_estructura() -> dict:
    """
    Verifica que existan todas las carpetas requeridas y las subcarpetas
    por clase en dataset_original, dataset/train y dataset/test.

    Returns
    -------
    dict con resumen de validación de estructura.
    """
    _titulo("1. VALIDACIÓN DE ESTRUCTURA DE CARPETAS")

    resultados = {
        "dataset_original": DATASET_ORIGINAL_DIR.exists(),
        "dataset_train": TRAIN_DIR.exists(),
        "dataset_test": TEST_DIR.exists(),
        "clases_train": {},
        "clases_test": {},
        "clases_original": {},
        "estructura_ok": True,
    }

    # Directorios raíz
    raices = {
        "dataset_original": DATASET_ORIGINAL_DIR,
        "dataset/train": TRAIN_DIR,
        "dataset/test": TEST_DIR,
    }
    for nombre, ruta in raices.items():
        estado = "✅" if ruta.exists() else "❌"
        print(f"  {estado} {nombre:30s}  {ruta}")
        if not ruta.exists():
            resultados["estructura_ok"] = False

    # Subcarpetas por clase en train y test
    for split_name, split_dir, key in [
        ("train", TRAIN_DIR, "clases_train"),
        ("test", TEST_DIR, "clases_test"),
    ]:
        _subtitulo(f"Subcarpetas en dataset/{split_name}")
        for clase in CLASS_NAMES:
            ruta_clase = split_dir / clase
            existe = ruta_clase.exists()
            estado = "✅" if existe else "❌"
            n = len(_listar_imagenes(ruta_clase)) if existe else 0
            print(f"    {estado} {clase:<22} ({n} imágenes)")
            resultados[key][clase] = existe
            if not existe:
                resultados["estructura_ok"] = False

    # Subcarpetas de dataset_original (usando CLASS_FOLDER_MAP)
    _subtitulo("Subcarpetas en dataset_original")
    for carpeta_orig, clase_limpia in CLASS_FOLDER_MAP.items():
        ruta = DATASET_ORIGINAL_DIR / carpeta_orig
        existe = ruta.exists()
        estado = "✅" if existe else "❌"
        n = len(_listar_imagenes(ruta)) if existe else 0
        print(f"    {estado} {carpeta_orig:<50} ({n} imgs → {clase_limpia})")
        resultados["clases_original"][clase_limpia] = existe

    estado_global = "✅ Estructura completa" if resultados["estructura_ok"] else \
                    "⚠️  Faltan carpetas"
    print(f"\n  Estado: {estado_global}")

    return resultados


# ══════════════════════════════════════════════════════════════════════════════
#  2. CONTEO DE IMÁGENES POR CLASE
# ══════════════════════════════════════════════════════════════════════════════

def contar_imagenes_por_clase() -> pd.DataFrame:
    """
    Genera tabla resumen con conteos por clase en original, train y test.

    Returns
    -------
    pd.DataFrame con columnas: Clase, Original, Train, Test, Total_usado,
                                Pct_train, Pct_test
    """
    _titulo("2. CONTEO DE IMÁGENES POR CLASE")

    filas = []
    for clase in CLASS_NAMES:
        # Buscar carpeta original (puede tener nombre largo)
        n_orig = 0
        for carpeta_orig, clase_limpia in CLASS_FOLDER_MAP.items():
            if clase_limpia == clase:
                n_orig = len(_listar_imagenes(DATASET_ORIGINAL_DIR / carpeta_orig))
                break

        n_train = len(_listar_imagenes(TRAIN_DIR / clase))
        n_test  = len(_listar_imagenes(TEST_DIR / clase))
        total   = n_train + n_test
        pct_t   = n_train / total * 100 if total > 0 else 0.0
        pct_te  = n_test  / total * 100 if total > 0 else 0.0

        filas.append({
            "Clase":        clase,
            "Original":     n_orig,
            "Train":        n_train,
            "Test":         n_test,
            "Total_usado":  total,
            "Pct_train":    round(pct_t, 1),
            "Pct_test":     round(pct_te, 1),
        })

    df = pd.DataFrame(filas)

    # Mostrar tabla
    print(f"\n  {'Clase':<18} {'Original':>9} {'Train':>7} {'Test':>6} "
          f"{'Usado':>7} {'%Train':>7} {'%Test':>6}")
    print("  " + "─" * 58)
    for _, row in df.iterrows():
        print(f"  {row['Clase']:<18} {row['Original']:>9} {row['Train']:>7} "
              f"{row['Test']:>6} {row['Total_usado']:>7} "
              f"{row['Pct_train']:>6.1f}% {row['Pct_test']:>5.1f}%")

    tot_orig  = df["Original"].sum()
    tot_train = df["Train"].sum()
    tot_test  = df["Test"].sum()
    tot_total = df["Total_usado"].sum()
    print("  " + "─" * 58)
    print(f"  {'TOTAL':<18} {tot_orig:>9} {tot_train:>7} {tot_test:>6} {tot_total:>7}")

    # Balance
    _subtitulo("Análisis de balance")
    counts = df["Total_usado"].values
    ratio_max_min = counts.max() / counts.min() if counts.min() > 0 else float("inf")
    print(f"  Ratio max/min de imágenes físicas: {ratio_max_min:.2f}")
    if ratio_max_min <= BALANCE_RATIO_THRESHOLD:
        print(f"  ✅ Dataset físico balanceado (ratio ≤ {BALANCE_RATIO_THRESHOLD})")
    else:
        print(f"  ⚠️  Dataset físico desbalanceado — se balanceará dinámicamente durante entrenamiento")
        print(f"  🎯 Target: {TARGET_TRAIN_SAMPLES_PER_CLASS} muestras por clase mediante aumento en memoria")
    print(f"  ℹ️  Las muestras aumentadas no existen como archivos físicos")

    return df


# ══════════════════════════════════════════════════════════════════════════════
#  3. VALIDACIÓN DE FORMATO
# ══════════════════════════════════════════════════════════════════════════════

def validar_formatos() -> list[dict]:
    """
    Detecta archivos con extensiones no válidas en train y test.

    Returns
    -------
    Lista de dicts con archivos inválidos.
    """
    _titulo("3. VALIDACIÓN DE FORMATO DE ARCHIVOS")

    invalidos = []
    total_revisados = 0

    for split_name, split_dir in [("train", TRAIN_DIR), ("test", TEST_DIR)]:
        for clase in CLASS_NAMES:
            clase_dir = split_dir / clase
            if not clase_dir.exists():
                continue
            for archivo in clase_dir.iterdir():
                if not archivo.is_file():
                    continue
                total_revisados += 1
                if archivo.suffix.lower() not in IMAGE_EXTENSIONS:
                    invalidos.append({
                        "split":    split_name,
                        "clase":    clase,
                        "archivo":  archivo.name,
                        "ruta":     str(archivo),
                        "extension": archivo.suffix,
                    })

    print(f"\n  Total archivos revisados : {total_revisados}")
    print(f"  Archivos con formato inválido: {len(invalidos)}")

    if invalidos:
        print("\n  Archivos problemáticos:")
        for item in invalidos[:10]:
            print(f"    ❌ [{item['split']}][{item['clase']}] "
                  f"{item['archivo']}  ({item['extension']})")
        if len(invalidos) > 10:
            print(f"    ... y {len(invalidos) - 10} más (ver CSV)")
    else:
        print("  ✅ Todos los archivos tienen extensiones válidas.")

    return invalidos


# ══════════════════════════════════════════════════════════════════════════════
#  4. VALIDACIÓN DE IMÁGENES CORRUPTAS
# ══════════════════════════════════════════════════════════════════════════════

def validar_corruptas() -> list[dict]:
    """
    Intenta abrir cada imagen con PIL. Registra las que fallan.

    Returns
    -------
    Lista de dicts con imágenes corruptas.
    """
    _titulo("4. VALIDACIÓN DE IMÁGENES CORRUPTAS")

    corruptas = []
    total = 0
    errores_mostrados = 0

    for split_name, split_dir in [("train", TRAIN_DIR), ("test", TEST_DIR)]:
        for clase in CLASS_NAMES:
            clase_dir = split_dir / clase
            if not clase_dir.exists():
                continue
            imgs = _listar_imagenes(clase_dir)
            total += len(imgs)
            for img_path in imgs:
                try:
                    with Image.open(img_path) as im:
                        im.verify()         # detecta corrupción sin leer pixels
                except Exception as e:
                    corruptas.append({
                        "split":  split_name,
                        "clase":  clase,
                        "archivo": img_path.name,
                        "ruta":   str(img_path),
                        "error":  str(e)[:120],
                    })
                    if errores_mostrados < 5:
                        print(f"  ❌ [{split_name}][{clase}] "
                              f"{img_path.name}: {str(e)[:60]}")
                        errores_mostrados += 1

    print(f"\n  Total imágenes verificadas : {total}")
    print(f"  Imágenes corruptas         : {len(corruptas)}")

    if not corruptas:
        print("  ✅ No se encontraron imágenes corruptas.")

    return corruptas


# ══════════════════════════════════════════════════════════════════════════════
#  5. VALIDACIÓN DE DIMENSIONES Y MODOS DE COLOR
# ══════════════════════════════════════════════════════════════════════════════

def analizar_dimensiones() -> tuple[pd.DataFrame, dict]:
    """
    Calcula estadísticas de dimensiones, relación de aspecto y modo de color.

    Returns
    -------
    (DataFrame con detalle por imagen, dict con estadísticas globales)
    """
    _titulo("5. ANÁLISIS DE DIMENSIONES Y MODOS DE COLOR")

    registros = []
    n_ok = 0

    for split_name, split_dir in [("train", TRAIN_DIR), ("test", TEST_DIR)]:
        for clase in CLASS_NAMES:
            clase_dir = split_dir / clase
            if not clase_dir.exists():
                continue
            for img_path in _listar_imagenes(clase_dir):
                try:
                    with Image.open(img_path) as im:
                        w, h = im.size
                        modo = im.mode
                    registros.append({
                        "split":  split_name,
                        "clase":  clase,
                        "archivo": img_path.name,
                        "ancho":  w,
                        "alto":   h,
                        "aspecto": round(w / h, 3) if h > 0 else 0,
                        "modo":   modo,
                        "es_rgb": modo in ("RGB", "RGBA"),
                    })
                    n_ok += 1
                except Exception:
                    pass

    if not registros:
        print("  ⚠️  No se pudieron leer dimensiones.")
        return pd.DataFrame(), {}

    df = pd.DataFrame(registros)

    # Estadísticas
    anchos = df["ancho"].values
    altos  = df["alto"].values
    stats = {
        "total_analizadas":  len(df),
        "ancho_min":  int(anchos.min()),
        "ancho_max":  int(anchos.max()),
        "ancho_mean": round(float(anchos.mean()), 1),
        "alto_min":   int(altos.min()),
        "alto_max":   int(altos.max()),
        "alto_mean":  round(float(altos.mean()), 1),
        "n_rgb":       int((df["modo"] == "RGB").sum()),
        "n_rgba":      int((df["modo"] == "RGBA").sum()),
        "n_otros":     int((~df["modo"].isin(["RGB", "RGBA"])).sum()),
        "modos":       dict(Counter(df["modo"].tolist())),
    }

    _subtitulo("Estadísticas de dimensiones")
    print(f"  Total imágenes analizadas : {stats['total_analizadas']}")
    print(f"  Ancho   — min: {stats['ancho_min']}px, "
          f"max: {stats['ancho_max']}px, "
          f"promedio: {stats['ancho_mean']}px")
    print(f"  Alto    — min: {stats['alto_min']}px, "
          f"max: {stats['alto_max']}px, "
          f"promedio: {stats['alto_mean']}px")

    _subtitulo("Modos de color detectados")
    for modo, cnt in sorted(stats["modos"].items(), key=lambda x: -x[1]):
        icono = "✅" if modo == "RGB" else "⚠️ "
        print(f"    {icono} {modo:<10}: {cnt:>5} imágenes")

    if stats["n_otros"] > 0:
        print(f"\n  ⚠️  {stats['n_otros']} imágenes con modo no RGB/RGBA "
              "(se convertirán a RGB en el entrenamiento).")
    else:
        print("\n  ✅ Todos los modos son RGB o RGBA.")

    # Imágenes pequeñas
    umbral_w, umbral_h = IMG_SIZE
    muy_pequenas = df[(df["ancho"] < umbral_w) | (df["alto"] < umbral_h)]
    if len(muy_pequenas) > 0:
        print(f"\n  ⚠️  {len(muy_pequenas)} imágenes más pequeñas que "
              f"IMG_SIZE={IMG_SIZE} (serán escaladas).")
    else:
        print(f"\n  ✅ Todas las imágenes tienen dimensiones ≥ IMG_SIZE={IMG_SIZE}.")

    return df, stats


# ══════════════════════════════════════════════════════════════════════════════
#  6. DETECCIÓN DE DUPLICADOS
# ══════════════════════════════════════════════════════════════════════════════

def detectar_duplicados() -> list[dict]:
    """
    Detecta imágenes duplicadas por hash SHA-256 en train y test.

    Returns
    -------
    Lista de dicts con grupos de duplicados.
    """
    _titulo("6. DETECCIÓN DE DUPLICADOS")

    hashes: dict[str, list[dict]] = defaultdict(list)
    total = 0

    for split_name, split_dir in [("train", TRAIN_DIR), ("test", TEST_DIR)]:
        for clase in CLASS_NAMES:
            clase_dir = split_dir / clase
            if not clase_dir.exists():
                continue
            for img_path in _listar_imagenes(clase_dir):
                h = _hash_archivo(img_path)
                if h:
                    hashes[h].append({
                        "split": split_name,
                        "clase": clase,
                        "archivo": img_path.name,
                        "ruta": str(img_path),
                    })
                    total += 1

    duplicados = []
    grupos_dup = 0
    for h, grupo in hashes.items():
        if len(grupo) > 1:
            grupos_dup += 1
            for item in grupo:
                duplicados.append({**item, "hash": h[:16] + "...", "grupo": grupos_dup})

    print(f"\n  Total imágenes analizadas  : {total}")
    print(f"  Grupos de duplicados       : {grupos_dup}")
    print(f"  Imágenes duplicadas        : {len(duplicados)}")

    if duplicados:
        print("\n  Ejemplos de duplicados:")
        mostrados = set()
        for dup in duplicados[:8]:
            g = dup["grupo"]
            if g not in mostrados:
                print(f"    Grupo {g}:")
                mostrados.add(g)
            print(f"      [{dup['split']}][{dup['clase']}] {dup['archivo']}")
    else:
        print("  ✅ No se detectaron imágenes duplicadas.")

    return duplicados


# ══════════════════════════════════════════════════════════════════════════════
#  7. VISUALIZACIÓN — DISTRIBUCIÓN DE CLASES
# ══════════════════════════════════════════════════════════════════════════════

def graficar_distribucion(df_conteo: pd.DataFrame) -> None:
    """Genera gráficos de barras de distribución de clases."""
    _titulo("7. VISUALIZACIÓN DE DISTRIBUCIÓN DE CLASES")

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    colores_clases = {
        "Black_rot":   "#e74c3c",
        "Esca":        "#8e44ad",
        "Healthy":     "#27ae60",
        "Leaf_blight": "#f39c12",
    }
    colores = [colores_clases.get(c, "#3498db") for c in CLASS_NAMES]

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle("VineGuard AI — Distribución de Clases en el Dataset",
                 fontsize=14, fontweight="bold", y=1.01)

    # ── (0,0) Dataset original ────────────────────────────────────────────
    ax = axes[0, 0]
    ax.bar(df_conteo["Clase"], df_conteo["Original"], color=colores, edgecolor="white")
    ax.set_title("Dataset Original")
    ax.set_xlabel("Clase")
    ax.set_ylabel("Nº de imágenes")
    ax.tick_params(axis="x", rotation=20)
    for bar, v in zip(ax.patches, df_conteo["Original"]):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
                str(v), ha="center", va="bottom", fontsize=9)

    # ── (0,1) Train ───────────────────────────────────────────────────────
    ax = axes[0, 1]
    ax.bar(df_conteo["Clase"], df_conteo["Train"], color=colores, edgecolor="white")
    ax.set_title("dataset/train  (80 %)")
    ax.set_xlabel("Clase")
    ax.set_ylabel("Nº de imágenes")
    ax.tick_params(axis="x", rotation=20)
    for bar, v in zip(ax.patches, df_conteo["Train"]):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
                str(v), ha="center", va="bottom", fontsize=9)

    # ── (1,0) Test ────────────────────────────────────────────────────────
    ax = axes[1, 0]
    ax.bar(df_conteo["Clase"], df_conteo["Test"], color=colores, edgecolor="white")
    ax.set_title("dataset/test  (20 %)")
    ax.set_xlabel("Clase")
    ax.set_ylabel("Nº de imágenes")
    ax.tick_params(axis="x", rotation=20)
    for bar, v in zip(ax.patches, df_conteo["Test"]):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
                str(v), ha="center", va="bottom", fontsize=9)

    # ── (1,1) Comparación Train vs Test ──────────────────────────────────
    ax = axes[1, 1]
    x = np.arange(len(CLASS_NAMES))
    w = 0.35
    bars_t  = ax.bar(x - w/2, df_conteo["Train"], w,
                     label="Train", color="#2980b9", edgecolor="white")
    bars_te = ax.bar(x + w/2, df_conteo["Test"], w,
                     label="Test", color="#e67e22", edgecolor="white")
    ax.set_title("Comparación Train vs Test")
    ax.set_xlabel("Clase")
    ax.set_ylabel("Nº de imágenes")
    ax.set_xticks(x)
    ax.set_xticklabels(CLASS_NAMES, rotation=20)
    ax.legend()
    for bar in bars_t:
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
                str(int(bar.get_height())), ha="center", va="bottom", fontsize=8)
    for bar in bars_te:
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
                str(int(bar.get_height())), ha="center", va="bottom", fontsize=8)

    plt.tight_layout()
    ruta = REPORTS_DIR / "distribucion_clases.png"
    fig.savefig(ruta, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  ✅ Guardado: {ruta}")


def graficar_dimensiones(df_dims: pd.DataFrame, stats: dict) -> None:
    """Genera gráficos de distribución de dimensiones y modos de color."""
    if df_dims.empty:
        return

    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    fig.suptitle("VineGuard AI — Distribución de Dimensiones y Modos de Color",
                 fontsize=13, fontweight="bold")

    # Distribución de anchos
    axes[0].hist(df_dims["ancho"], bins=30, color="#3498db", edgecolor="white")
    axes[0].axvline(IMG_SIZE[0], color="red", linestyle="--", label=f"IMG_SIZE={IMG_SIZE[0]}")
    axes[0].set_title("Distribución de Ancho (px)")
    axes[0].set_xlabel("Ancho (px)")
    axes[0].set_ylabel("Frecuencia")
    axes[0].legend()

    # Distribución de altos
    axes[1].hist(df_dims["alto"], bins=30, color="#2ecc71", edgecolor="white")
    axes[1].axvline(IMG_SIZE[1], color="red", linestyle="--", label=f"IMG_SIZE={IMG_SIZE[1]}")
    axes[1].set_title("Distribución de Alto (px)")
    axes[1].set_xlabel("Alto (px)")
    axes[1].set_ylabel("Frecuencia")
    axes[1].legend()

    # Modos de color
    modos = stats.get("modos", {})
    if modos:
        nombres_modo = list(modos.keys())
        conteos_modo = list(modos.values())
        colores_modo = ["#27ae60" if m == "RGB" else "#e74c3c" for m in nombres_modo]
        axes[2].bar(nombres_modo, conteos_modo, color=colores_modo, edgecolor="white")
        axes[2].set_title("Modos de Color")
        axes[2].set_xlabel("Modo")
        axes[2].set_ylabel("Cantidad")
        for bar, v in zip(axes[2].patches, conteos_modo):
            axes[2].text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
                         str(v), ha="center", va="bottom", fontsize=9)

    plt.tight_layout()
    ruta = REPORTS_DIR / "distribucion_dimensiones.png"
    fig.savefig(ruta, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  ✅ Guardado: {ruta}")


# ══════════════════════════════════════════════════════════════════════════════
#  8. VISUALIZACIÓN DE MUESTRAS POR CLASE
# ══════════════════════════════════════════════════════════════════════════════

def visualizar_muestras(n_muestras: int = 5) -> None:
    """
    Genera un grid con n_muestras imágenes aleatorias por clase del train.
    """
    _titulo("8. VISUALIZACIÓN DE MUESTRAS POR CLASE")

    random.seed(SEED)
    n_clases = len(CLASS_NAMES)

    fig = plt.figure(figsize=(n_muestras * 3, n_clases * 3 + 0.5))
    fig.suptitle("VineGuard AI — Muestras por Clase (dataset/train)",
                 fontsize=13, fontweight="bold")

    gs = gridspec.GridSpec(n_clases, n_muestras, figure=fig,
                           hspace=0.5, wspace=0.1)

    for fila, clase in enumerate(CLASS_NAMES):
        clase_dir = TRAIN_DIR / clase
        imagenes = _listar_imagenes(clase_dir)

        if not imagenes:
            print(f"  ⚠️  Sin imágenes en train/{clase}")
            continue

        muestra = random.sample(imagenes, min(n_muestras, len(imagenes)))

        for col, img_path in enumerate(muestra):
            ax = fig.add_subplot(gs[fila, col])
            try:
                with Image.open(img_path) as im:
                    w, h = im.size
                    img_rgb = im.convert("RGB")
                ax.imshow(img_rgb)
                ax.axis("off")
                if col == 0:
                    ax.text(-0.08, 0.5, clase, transform=ax.transAxes,
                            fontsize=10, fontweight="bold",
                            ha="right", va="center")
                ax.set_title(f"{w}×{h}", fontsize=7, color="#555555")
            except Exception as e:
                ax.text(0.5, 0.5, "Error", ha="center", va="center",
                        transform=ax.transAxes, color="red")
                ax.axis("off")

    plt.subplots_adjust(left=0.15)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    ruta = REPORTS_DIR / "muestras_por_clase.png"
    fig.savefig(ruta, dpi=130, bbox_inches="tight")
    plt.close(fig)
    print(f"  ✅ Guardado: {ruta}")


# ══════════════════════════════════════════════════════════════════════════════
#  9. GUARDAR REPORTES CSV
# ══════════════════════════════════════════════════════════════════════════════

def generar_estadisticas_descriptivas(df_conteo: pd.DataFrame) -> dict:
    """Genera estadísticas descriptivas detalladas del dataset."""
    counts = df_conteo["Total_usado"].values
    stats = {
        "Total imágenes": int(df_conteo["Total_usado"].sum()),
        "Número de clases": len(counts),
        "Media por clase": round(float(np.mean(counts)), 2),
        "Desviación estándar": round(float(np.std(counts, ddof=1)), 2),
        "Mínimo": int(counts.min()),
        "Máximo": int(counts.max()),
        "Q1 (25%)": float(np.percentile(counts, 25)),
        "Mediana (Q2)": float(np.median(counts)),
        "Q3 (75%)": float(np.percentile(counts, 75)),
        "Rango": int(counts.max() - counts.min()),
        "Rango intercuartílico (IQR)": float(np.percentile(counts, 75) - np.percentile(counts, 25)),
        "Porcentaje clase mayoritaria": round(counts.max() / counts.sum() * 100, 2),
        "Porcentaje clase minoritaria": round(counts.min() / counts.sum() * 100, 2),
    }
    return stats


def guardar_reportes_csv(
    df_conteo: pd.DataFrame,
    invalidos: list[dict],
    corruptas: list[dict],
    duplicados: list[dict],
    df_dims: pd.DataFrame,
    stats_dims: dict,
) -> None:
    """Guarda todos los reportes CSV en reports/eda/."""
    _titulo("9. GENERACIÓN DE REPORTES CSV")

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    # 9.1 Resumen del dataset
    ruta = REPORTS_DIR / "resumen_dataset.csv"
    df_conteo.to_csv(ruta, index=False, encoding="utf-8")
    print(f"  ✅ {ruta.name}")

    # 9.1b Estadísticas descriptivas detalladas
    ruta = REPORTS_DIR / "estadisticas_descriptivas.csv"
    stats_desc = generar_estadisticas_descriptivas(df_conteo)
    filas_desc = [{"estadistica": k, "valor": v} for k, v in stats_desc.items()]
    _guardar_csv(ruta, filas_desc, ["estadistica", "valor"])
    print(f"  ✅ {ruta.name}")

    # 9.2 Imágenes con formato inválido
    ruta = REPORTS_DIR / "imagenes_invalidas.csv"
    if invalidos:
        _guardar_csv(ruta, invalidos, ["split", "clase", "archivo", "ruta", "extension"])
    else:
        _guardar_csv(ruta, [{"info": "Sin archivos con formato inválido"}], ["info"])
    print(f"  ✅ {ruta.name}")

    # 9.3 Imágenes corruptas
    ruta = REPORTS_DIR / "imagenes_corruptas.csv"
    if corruptas:
        _guardar_csv(ruta, corruptas, ["split", "clase", "archivo", "ruta", "error"])
    else:
        _guardar_csv(ruta, [{"info": "Sin imágenes corruptas"}], ["info"])
    print(f"  ✅ {ruta.name}")

    # 9.4 Duplicados
    ruta = REPORTS_DIR / "imagenes_duplicadas.csv"
    if duplicados:
        _guardar_csv(ruta, duplicados, ["grupo", "split", "clase", "archivo", "ruta", "hash"])
    else:
        _guardar_csv(ruta, [{"info": "Sin duplicados"}], ["info"])
    print(f"  ✅ {ruta.name}")

    # 9.5 Estadísticas de dimensiones (resumen global)
    ruta = REPORTS_DIR / "estadisticas_dimensiones.csv"
    if stats_dims:
        filas_stats = [
            {"metrica": k, "valor": v}
            for k, v in stats_dims.items()
            if not isinstance(v, dict)
        ]
        _guardar_csv(ruta, filas_stats, ["metrica", "valor"])
    else:
        _guardar_csv(ruta, [{"info": "Sin datos de dimensiones"}], ["info"])
    print(f"  ✅ {ruta.name}")

    # 9.6 Detalle de dimensiones por imagen
    if not df_dims.empty:
        ruta_detalle = REPORTS_DIR / "detalle_dimensiones.csv"
        df_dims.to_csv(ruta_detalle, index=False, encoding="utf-8")
        print(f"  ✅ {ruta_detalle.name}  ({len(df_dims)} filas)")


# ══════════════════════════════════════════════════════════════════════════════
#  10. REPORTE FINAL EN CONSOLA
# ══════════════════════════════════════════════════════════════════════════════

def reporte_final(
    estructura: dict,
    df_conteo: pd.DataFrame,
    invalidos: list[dict],
    corruptas: list[dict],
    duplicados: list[dict],
    stats_dims: dict,
) -> bool:
    _titulo("10. REPORTE FINAL — EDA Y VALIDACIÓN DE DATOS", char="═")

    stats_desc = generar_estadisticas_descriptivas(df_conteo)
    counts = df_conteo["Total_usado"].values
    ratio = float(counts.max() / counts.min()) if counts.min() > 0 else 999.0
    balanceado = ratio <= BALANCE_RATIO_THRESHOLD
    tot_orig = int(df_conteo["Original"].sum())
    tot_train = int(df_conteo["Train"].sum())
    tot_test = int(df_conteo["Test"].sum())
    n_clases = int((df_conteo["Total_usado"] > 0).sum())
    pct_train = tot_train / (tot_train + tot_test) * 100 if (tot_train + tot_test) > 0 else 0
    n_no_rgb = stats_dims.get("n_otros", 0)

    print(f"""
============================================================
  EDA Y VALIDACIÓN DE DATOS — VineGuard AI
============================================================
  Total de imágenes          : {stats_desc['Total imágenes']}
  Clases detectadas          : {', '.join(df_conteo['Clase'].tolist())}
  Media de imágenes por clase: {stats_desc['Media por clase']}
  Desviación estándar        : {stats_desc['Desviación estándar']}
  Mínimo                     : {stats_desc['Mínimo']}
  Máximo                     : {stats_desc['Máximo']}
  Q1                         : {stats_desc['Q1 (25%)']}
  Mediana                    : {stats_desc['Mediana (Q2)']}
  Q3                         : {stats_desc['Q3 (75%)']}
  Rango                      : {stats_desc['Rango']}
  Rango intercuartílico      : {stats_desc['Rango intercuartílico (IQR)']}

  Distribución train/test:
    Train: {tot_train} ({pct_train:.1f}%)
    Test:  {tot_test} ({100-pct_train:.1f}%)

  Balance del dataset:
    {'✅ Balanceado (físico)' if balanceado else f'⚠️  Físicamente desbalanceado (ratio {ratio:.2f}) — se aplicará balanceo dinámico solo en train'}

  Estado del dataset:
""")

    balanceo_configurado = (
        isinstance(TARGET_TRAIN_SAMPLES_PER_CLASS, int)
        and TARGET_TRAIN_SAMPLES_PER_CLASS > 0
    )

    criterios = {
        "Estructura de carpetas completa":    estructura["estructura_ok"],
        f"Las {len(CLASS_NAMES)} clases presentes": n_clases == len(CLASS_NAMES),
        "Sin imágenes corruptas":             len(corruptas) == 0,
        "Sin archivos con formato inválido":  len(invalidos) == 0,
        "División train/test cercana a 80/20": abs(pct_train - 80) <= 5,
    }

    todos_ok = True
    for criterio, ok in criterios.items():
        icono = "✅" if ok else "⚠️ "
        print(f"  {icono} {criterio}")
        if not ok:
            todos_ok = False

    print(f"  ℹ️  Target configurado para entrenamiento: {TARGET_TRAIN_SAMPLES_PER_CLASS} muestras/clase")
    if balanceo_configurado:
        print(f"  ℹ️  Balanceo dinámico configurado para el entrenamiento")
    else:
        print(f"  ⚠️  Balanceo dinámico NO configurado correctamente")

    print()

    if not balanceado:
        print(f"  ⚠️  Advertencia: dataset desbalanceado (ratio {ratio:.2f})")
        print(f"  ℹ️  El balanceo se aplicará solo en train. Test conserva su distribución original.")

    print(f"  {'✅ Dataset estructuralmente válido para entrenamiento' if todos_ok else '⚠️  Dataset requiere revisión'}")
    print(f"  Reportes guardados en: {REPORTS_DIR}")
    print(f"  Análisis completado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * SECTION_WIDTH)

    return todos_ok


# ══════════════════════════════════════════════════════════════════════════════
#  FUNCIÓN PRINCIPAL
# ══════════════════════════════════════════════════════════════════════════════

def main() -> None:
    print("\n" + "═" * SECTION_WIDTH)
    print("  EDA Y VALIDACIÓN DE DATOS — VineGuard AI")
    print(f"  Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("═" * SECTION_WIDTH)
    print(f"\n  Directorio del proyecto : {DATASET_ORIGINAL_DIR.parent}")
    print(f"  Clases objetivo         : {CLASS_NAMES}")
    print(f"  IMG_SIZE                : {IMG_SIZE}")
    print(f"  SEED                    : {SEED}")

    # 1. Estructura
    estructura = validar_estructura()

    # 2. Conteo por clase
    df_conteo = contar_imagenes_por_clase()

    # 3. Formatos
    invalidos = validar_formatos()

    # 4. Corruptas
    corruptas = validar_corruptas()

    # 5. Dimensiones
    df_dims, stats_dims = analizar_dimensiones()

    # 6. Duplicados
    duplicados = detectar_duplicados()

    # 7. Gráficos de distribución
    graficar_distribucion(df_conteo)
    graficar_dimensiones(df_dims, stats_dims)

    # 8. Muestras por clase
    visualizar_muestras(n_muestras=5)

    # 9. CSV
    guardar_reportes_csv(
        df_conteo, invalidos, corruptas, duplicados, df_dims, stats_dims
    )

    # 10. Reporte final
    dataset_valido = reporte_final(
        estructura, df_conteo, invalidos, corruptas, duplicados, stats_dims
    )

    sys.exit(0 if dataset_valido else 1)


if __name__ == "__main__":
    main()