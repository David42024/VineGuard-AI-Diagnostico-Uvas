"""
preprocesamiento_aumento.py
Preprocesamiento y aumento de datos — VineGuard AI

Funcionalidades:
  - Redimensionar imágenes a IMG_SIZE (224, 224)
  - Conversión a RGB
  - Normalización de píxeles
  - Aumento de datos solo para entrenamiento
  - Generación de ejemplos visuales en reports/preprocessing/
"""

import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
elif hasattr(sys.stdout, 'buffer'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mantenedor import IMG_SIZE, TRAIN_DIR, CLASS_NAMES, PREPROCESSING_DIR, SEED

np.random.seed(SEED)


def redimensionar_imagen(img: Image.Image, target_size: tuple = IMG_SIZE) -> Image.Image:
    return img.resize(target_size, Image.Resampling.LANCZOS)


def convertir_a_rgb(img: Image.Image) -> Image.Image:
    return img.convert("RGB")


def normalizar_pixeles(arr: np.ndarray) -> np.ndarray:
    arr = arr.astype(np.float32)
    if arr.max() > 1.0:
        arr /= 255.0
    return arr


class DataAugmenter:
    def __init__(self, target_size: tuple = IMG_SIZE):
        self.target_size = target_size

    def rotacion(self, img: Image.Image, angle: float = 30) -> Image.Image:
        return img.rotate(np.random.uniform(-angle, angle), resample=Image.Resampling.BILINEAR)

    def brillo(self, img: Image.Image, factor_range: tuple = (0.6, 1.4)) -> Image.Image:
        factor = np.random.uniform(*factor_range)
        enhancer = img if img.mode == "RGB" else img.convert("RGB")
        arr = np.array(enhancer, dtype=np.float32) * factor
        arr = np.clip(arr, 0, 255).astype(np.uint8)
        return Image.fromarray(arr)

    def zoom(self, img: Image.Image, zoom_range: tuple = (0.85, 1.15)) -> Image.Image:
        factor = np.random.uniform(*zoom_range)
        w, h = img.size
        nw = max(1, int(w * factor))
        nh = max(1, int(h * factor))
        if factor < 1:
            reducida = img.resize((nw, nh), Image.Resampling.LANCZOS)
            fondo = Image.new("RGB", (w, h), (0, 0, 0))
            left = (w - nw) // 2
            top = (h - nh) // 2
            fondo.paste(reducida, (left, top))
            return fondo
        ampliada = img.resize((nw, nh), Image.Resampling.LANCZOS)
        left = (nw - w) // 2
        top = (nh - h) // 2
        return ampliada.crop((left, top, left + w, top + h))

    def contraste(self, img: Image.Image, factor_range: tuple = (0.6, 1.4)) -> Image.Image:
        factor = np.random.uniform(*factor_range)
        arr = np.array(img.convert("RGB"), dtype=np.float32)
        mean = arr.mean(axis=(0, 1), keepdims=True)
        arr = mean + factor * (arr - mean)
        arr = np.clip(arr, 0, 255).astype(np.uint8)
        return Image.fromarray(arr)

    def desplazamiento(self, img: Image.Image, max_shift: float = 0.1) -> Image.Image:
        w, h = img.size
        dx = int(np.random.uniform(-max_shift, max_shift) * w)
        dy = int(np.random.uniform(-max_shift, max_shift) * h)
        return img.transform(img.size, Image.AFFINE, (1, 0, dx, 0, 1, dy), resample=Image.Resampling.BILINEAR)

    def volteo_horizontal(self, img: Image.Image) -> Image.Image:
        if np.random.random() > 0.5:
            return img.transpose(Image.FLIP_LEFT_RIGHT)
        return img

    def escalado(self, img: Image.Image, scale_range: tuple = (0.9, 1.1)) -> Image.Image:
        factor = np.random.uniform(*scale_range)
        w, h = img.size
        nw, nh = int(w * factor), int(h * factor)
        img = img.resize((nw, nh), Image.Resampling.LANCZOS)
        if factor > 1:
            left = (nw - w) // 2
            top = (nh - h) // 2
            img = img.crop((left, top, left + w, top + h))
        else:
            bg = Image.new("RGB", (w, h), (0, 0, 0))
            left = (w - nw) // 2
            top = (h - nh) // 2
            bg.paste(img, (left, top))
            img = bg
        return img

    def aplicar_aumentos(self, img: Image.Image) -> Image.Image:
        if np.random.random() < 0.7:
            img = self.rotacion(img, angle=20)
        if np.random.random() < 0.6:
            img = self.brillo(img, factor_range=(0.8, 1.2))
        if np.random.random() < 0.5:
            img = self.zoom(img, zoom_range=(0.9, 1.1))
        if np.random.random() < 0.5:
            img = self.contraste(img, factor_range=(0.8, 1.2))
        if np.random.random() < 0.4:
            img = self.desplazamiento(img, max_shift=0.05)
        if np.random.random() < 0.5:
            img = self.volteo_horizontal(img)
        return img


def generar_ejemplos_visuales():
    PREPROCESSING_DIR.mkdir(parents=True, exist_ok=True)
    augmenter = DataAugmenter()

    clases_con_imagenes = []
    for clase in CLASS_NAMES:
        clase_dir = TRAIN_DIR / clase
        if not clase_dir.exists():
            continue
        imgs = [p for p in clase_dir.iterdir() if p.suffix.lower() in {".jpg", ".jpeg", ".png"}]
        if imgs:
            clases_con_imagenes.append((clase, imgs[0]))

    if not clases_con_imagenes:
        print("  ⚠️  No se encontraron imágenes para generar ejemplos.")
        return

    n = len(clases_con_imagenes)

    # Rotacion — una fila por clase
    fig, axes = plt.subplots(n, 4, figsize=(12, 3 * n))
    if n == 1:
        axes = [axes]
    for fila, (clase, img_path) in enumerate(clases_con_imagenes):
        original = Image.open(img_path).convert("RGB").resize(IMG_SIZE, Image.Resampling.LANCZOS)
        axs = axes[fila]
        axs[0].imshow(original)
        axs[0].set_title("Original")
        axs[0].axis("off")
        for i, ang in enumerate([15, 30, -20], 1):
            rot = original.rotate(ang, resample=Image.Resampling.BILINEAR)
            axs[i].imshow(rot)
            axs[i].set_title(f"Rot {ang}°")
            axs[i].axis("off")
        axs[0].text(-0.08, 0.5, clase, transform=axs[0].transAxes,
                    fontsize=9, fontweight="bold", ha="right", va="center")
    plt.tight_layout()
    fig.savefig(PREPROCESSING_DIR / "ejemplos_rotacion.png", dpi=130, bbox_inches="tight")
    plt.close(fig)

    # Brillo — una fila por clase
    fig, axes = plt.subplots(n, 4, figsize=(12, 3 * n))
    if n == 1:
        axes = [axes]
    for fila, (clase, img_path) in enumerate(clases_con_imagenes):
        original = Image.open(img_path).convert("RGB").resize(IMG_SIZE, Image.Resampling.LANCZOS)
        axs = axes[fila]
        axs[0].imshow(original)
        axs[0].set_title("Original")
        axs[0].axis("off")
        for i, fac in enumerate([0.6, 1.0, 1.4], 1):
            arr = np.array(original, dtype=np.float32) * fac
            arr = np.clip(arr, 0, 255).astype(np.uint8)
            axs[i].imshow(arr)
            axs[i].set_title(f"Factor {fac}")
            axs[i].axis("off")
        axs[0].text(-0.08, 0.5, clase, transform=axs[0].transAxes,
                    fontsize=9, fontweight="bold", ha="right", va="center")
    plt.tight_layout()
    fig.savefig(PREPROCESSING_DIR / "ejemplos_brillo.png", dpi=130, bbox_inches="tight")
    plt.close(fig)

    # Aumento completo — una fila por clase
    fig, axes = plt.subplots(n, 4, figsize=(14, 3 * n))
    if n == 1:
        axes = [axes]
    for fila, (clase, img_path) in enumerate(clases_con_imagenes):
        original = Image.open(img_path).convert("RGB").resize(IMG_SIZE, Image.Resampling.LANCZOS)
        axs = axes[fila]
        for i in range(4):
            aug = augmenter.aplicar_aumentos(original)
            axs[i].imshow(aug)
            if fila == 0:
                axs[i].set_title(f"Aumento {i+1}")
            axs[i].axis("off")
        axs[0].text(-0.08, 0.5, clase, transform=axs[0].transAxes,
                    fontsize=9, fontweight="bold", ha="right", va="center")
    plt.tight_layout()
    fig.savefig(PREPROCESSING_DIR / "ejemplos_aumento_datos.png", dpi=130, bbox_inches="tight")
    plt.close(fig)

    print(f"  Ejemplos visuales guardados en: {PREPROCESSING_DIR}")


def pipeline_preprocesamiento(imagen: Image.Image) -> np.ndarray:
    img = convertir_a_rgb(imagen)
    img = redimensionar_imagen(img)
    arr = np.array(img, dtype=np.float32)
    arr = normalizar_pixeles(arr)
    return arr


def pipeline_aumento(imagen: Image.Image) -> np.ndarray:
    augmenter = DataAugmenter()
    img = convertir_a_rgb(imagen)
    img = redimensionar_imagen(img)
    img = augmenter.aplicar_aumentos(img)
    arr = np.array(img, dtype=np.float32)
    arr = normalizar_pixeles(arr)
    return arr


if __name__ == "__main__":
    print("=" * 60)
    print("  Preprocesamiento y Aumento de Datos — VineGuard AI")
    print("=" * 60)
    generar_ejemplos_visuales()
    print("Completado.")
