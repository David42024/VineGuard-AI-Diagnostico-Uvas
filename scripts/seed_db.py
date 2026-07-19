"""Seed database with default users, models, and sample diagnostics."""
import sys
import json
import random
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.database.session import SessionLocal
from backend.database.models import UserModel, DiagnosticModel, AuditLogModel, ModelModel
from backend.core.security import hash_password

SEED_IMAGES_DIR = Path(__file__).resolve().parent.parent / "data" / "seed_images"

USERS = [
    {"name": "Administrador", "username": "admin", "password": "admin123", "role": "admin"},
    {"name": "Usuario", "username": "usuario", "password": "12345", "role": "client"},
    {"name": "Ana García", "username": "agarcia", "password": "12345", "role": "client"},
    {"name": "Carlos López", "username": "clopez", "password": "12345", "role": "client"},
]

# Actual prediction modes supported by the backend
PREDICTION_MODES = [
    {"key": "consensus", "name": "Consenso", "description": "Combina múltiples modelos por votación"},
    {"key": "best_model", "name": "Mejor Modelo", "description": "Usa el modelo ganador del entrenamiento"},
    {"key": "all", "name": "Todos los Modelos", "description": "Ejecuta todos los modelos y compara resultados"},
]

DISEASES = ["Healthy", "Black_rot", "Esca", "Leaf_blight"]

DISEASE_FILENAMES = {
    "Healthy": ["hoja_sana_01.jpg", "hoja_sana_02.jpg", "hoja_sana_03.jpg", "vitis_verde_01.jpg", "parra_ok_01.jpg"],
    "Black_rot": ["black_rot_01.jpg", "podredumbre_01.jpg", "black_rot_02.jpg", "mancha_negra_01.jpg"],
    "Esca": ["esca_01.jpg", "esca_02.jpg", "enfermedad_madera_01.jpg", "apoplejia_01.jpg"],
    "Leaf_blight": ["leaf_blight_01.jpg", "tizon_01.jpg", "isariopsis_01.jpg", "mancha_hoja_01.jpg"],
}

DISEASE_COLORS = {
    "Healthy": (76, 175, 80),
    "Black_rot": (33, 33, 33),
    "Esca": (121, 85, 72),
    "Leaf_blight": (255, 152, 0),
}

SEED_MODEL_FILES = [
    ("models/cnn_feature_extractor.h5", "Extractor CNN (H1)"),
    ("models/cnn_svm_model.pkl", "Clasificador SVM (H1)"),
    ("models/svm_model.pkl", "Modelo SVM (M1)"),
    ("models/random_forest_model.pkl", "Modelo Random Forest (M2)"),
    ("models/knn_model.pkl", "Modelo KNN (M3)"),
    ("models/transfer_random_forest_model.pkl", "Modelo Transfer+RF (H2)"),
    ("models/transfer_feature_extractor.h5", "Extractor Transfer (H2)"),
    ("models/modelo_final/h1_cnn_feature_extractor.h5", "Extractor CNN final (H1)"),
    ("models/modelo_final/h1_svm_classifier.pkl", "SVM final (H1)"),
    ("reports/modelos/tuning/mejor_m1_svm_tuning.pkl", "SVM Tuning (M1)"),
    ("reports/modelos/tuning/mejor_m2_random_forest_tuning.pkl", "RF Tuning (M2)"),
    ("reports/modelos/tuning/mejor_m3_knn_tuning.pkl", "KNN Tuning (M3)"),
    ("reports/modelos/tuning/mejor_h2_transfer_rf_tuning.pkl", "Transfer+RF Tuning (H2)"),
    ("reports/modelos/tuning/transfer_feature_extractor.keras", "Extractor Transfer Tuning (H2)"),
]


def random_date(days_back: int) -> datetime:
    now = datetime.utcnow()
    past = now - timedelta(days=days_back)
    return past + timedelta(seconds=random.randint(0, int((now - past).total_seconds())))


def _generate_placeholder_images():
    SEED_IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    from PIL import Image
    for disease, filenames in DISEASE_FILENAMES.items():
        color = DISEASE_COLORS.get(disease, (128, 128, 128))
        for name in filenames:
            path = SEED_IMAGES_DIR / name
            if not path.exists():
                img = Image.new("RGB", (224, 224), color)
                img.save(str(path), "JPEG", quality=75)
    count = sum(len(v) for v in DISEASE_FILENAMES.values())
    print(f"✓ {count} imágenes placeholder generadas en {SEED_IMAGES_DIR}")


def verify_model_files():
    """Check that all expected model artifacts exist on disk."""
    root = Path(__file__).resolve().parent.parent
    missing = []
    ok = 0
    for rel_path, label in SEED_MODEL_FILES:
        full = root / rel_path
        if full.exists():
            ok += 1
        else:
            missing.append(f"  {label}: {rel_path}")
    if missing:
        print(f"⚠ {len(missing)} archivos faltantes (pueden no afectar los 3 modos):")
        for m in missing:
            print(m)
    print(f"✓ {ok}/{len(SEED_MODEL_FILES)} archivos de modelo verificados")


def verify_prediction_modes():
    """Quick verification that each mode can load its dependencies."""
    print("\n--- Verificando modos de predicción ---")
    root = Path(__file__).resolve().parent.parent

    # best_model — check modelo_final.json + its artifacts
    final_json = root / "models" / "modelo_final" / "modelo_final.json"
    if final_json.exists():
        with open(final_json) as f:
            data = json.load(f)
        winner = data.get("modelo_ganador", "desconocido")
        final_extractor = root / "models" / "modelo_final" / "h1_cnn_feature_extractor.h5"
        final_clf = root / "models" / "modelo_final" / "h1_svm_classifier.pkl"
        best_artifacts_ok = final_extractor.exists() and final_clf.exists()
        print(f"  ✓ Mejor Modelo → {winner} (artefactos: {'✓' if best_artifacts_ok else '✗'})")
    else:
        print(f"  ✗ Mejor Modelo → {final_json} no encontrado")

    # consensus — check H1 (main) + M1 (fallback)
    h1_extractor = root / "models" / "cnn_feature_extractor.h5"
    h1_clf = root / "models" / "cnn_svm_model.pkl"
    m1 = root / "reports" / "modelos" / "tuning" / "mejor_m1_svm_tuning.pkl"
    h1_ok = h1_extractor.exists() and h1_clf.exists()
    m1_ok = m1.exists()
    print(f"  ✓ Consenso → H1 ({'✓' if h1_ok else '✗'}) M1 ({'✓' if m1_ok else '✗'})")

    # all — H1 + M1 + H2 + M2 + M3
    h2_artifacts = [
        root / "models" / "transfer_feature_extractor.h5",
        root / "reports" / "modelos" / "tuning" / "mejor_h2_transfer_rf_tuning.pkl",
    ]
    m2 = root / "reports" / "modelos" / "tuning" / "mejor_m2_random_forest_tuning.pkl"
    m3 = root / "reports" / "modelos" / "tuning" / "mejor_m3_knn_tuning.pkl"
    h2_ok = all(p.exists() for p in h2_artifacts)
    m2_ok = m2.exists()
    m3_ok = m3.exists()
    ok_count = sum([h1_ok, m1_ok, h2_ok, m2_ok, m3_ok])
    print(f"  ✓ Todos los Modelos → H1 ({'✓' if h1_ok else '✗'}) M1 ({'✓' if m1_ok else '✗'}) H2 ({'✓' if h2_ok else '✗'}) M2 ({'✓' if m2_ok else '✗'}) M3 ({'✓' if m3_ok else '✗'}) ({ok_count}/5)")

    print("--- Verificación completada ---\n")


def main(count: int = 50, verify: bool = True):
    _generate_placeholder_images()
    if verify:
        verify_model_files()
        verify_prediction_modes()

    db = SessionLocal()

    if db.query(UserModel).count() == 0:
        for u in USERS:
            db.add(UserModel(
                name=u["name"],
                username=u["username"],
                password_hash=hash_password(u["password"]),
                role=u["role"],
                created_at=random_date(60),
            ))
        db.commit()
        print(f"✓ {len(USERS)} usuarios creados")
    else:
        print("→ Usuarios ya existen, omitiendo")

    if db.query(ModelModel).count() == 0:
        for m in PREDICTION_MODES:
            db.add(ModelModel(
                name=m["name"],
                type=m["key"],
            ))
        db.commit()
        print(f"✓ {len(PREDICTION_MODES)} modos de predicción creados en DB")
    else:
        print("→ Modos de predicción ya existen en DB, omitiendo")

    missing_image = db.query(DiagnosticModel).filter(DiagnosticModel.image_path.is_(None)).all()
    if missing_image:
        for diag in missing_image:
            filename = diag.filename or "hoja_sana_01.jpg"
            diag.image_path = str(SEED_IMAGES_DIR / filename)
        db.commit()
        print(f"✓ {len(missing_image)} diagnósticos backfilled con image_path")

    if db.query(DiagnosticModel).count() == 0:
        users = db.query(UserModel).all()
        for _ in range(count):
            user = random.choice(users)
            disease = random.choice(DISEASES)
            mode = random.choice(PREDICTION_MODES)
            confidence = round(random.uniform(0.76, 0.99), 4)
            filename = random.choice(DISEASE_FILENAMES[disease])
            ts = random_date(30)

            probs = {
                d: round(confidence if d == disease else random.uniform(0.01, 0.15), 4)
                for d in DISEASES
            }

            db.add(DiagnosticModel(
                user_id=user.id,
                timestamp=ts,
                filename=filename,
                image_path=str(SEED_IMAGES_DIR / filename),
                result=disease,
                confidence=confidence,
                model_used=mode["name"],
                probabilities=json.dumps(probs),
                inference_time_ms=random.randint(150, 2500),
                analysis_type=mode["key"],
                status="completed",
                is_demo=1,
            ))

        for u in users:
            db.add(AuditLogModel(
                user_id=u.id,
                action="login",
                detail="Inicio de sesión exitoso",
                timestamp=random_date(30),
            ))

        db.commit()
        print(f"✓ {count} diagnósticos seed creados (modos: {', '.join(m['key'] for m in PREDICTION_MODES)})")
    else:
        existing = db.query(DiagnosticModel).count()
        print(f"→ Diagnósticos ya existen ({existing}), omitiendo creación nueva")

    db.close()
    print("✓ Seed completado")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=50, help="Número de diagnósticos seed")
    parser.add_argument("--no-verify", action="store_true", help="Saltar verificación de archivos")
    args = parser.parse_args()
    main(args.count, verify=not args.no_verify)
