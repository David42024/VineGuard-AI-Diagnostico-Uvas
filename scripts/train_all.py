"""Run all 5 model training scripts sequentially."""
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SCRIPTS = [
    "src/train_m1_svm.py",
    "src/train_m2_random_forest.py",
    "src/train_m3_knn.py",
    "src/train_h1_cnn_svm.py",
    "src/train_h2_transfer_random_forest.py",
]

for script in SCRIPTS:
    print(f"\n{'='*60}")
    print(f"Ejecutando: {script}")
    print(f"{'='*60}")
    result = subprocess.run(
        [sys.executable, str(BASE_DIR / script)],
        cwd=str(BASE_DIR),
        capture_output=True,
        text=True,
    )
    print(result.stdout[-1500:] if result.stdout else "")
    if result.returncode != 0:
        print(f"ERROR en {script}:")
        print(result.stderr[-1500:] if result.stderr else "Desconocido")
        sys.exit(1)
    else:
        print(f"✅ {script} completado")

print(f"\n{'='*60}")
print("Todos los modelos entrenados correctamente.")
print(f"{'='*60}")
