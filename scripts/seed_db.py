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

USERS = [
    {"name": "Administrador", "username": "admin", "password": "admin123", "role": "admin"},
    {"name": "Usuario", "username": "usuario", "password": "12345", "role": "client"},
    {"name": "Ana García", "username": "agarcia", "password": "12345", "role": "client"},
    {"name": "Carlos López", "username": "clopez", "password": "12345", "role": "client"},
]

MODELS = [
    {"name": "SVM (M1)", "type": "svm", "accuracy": 0.892, "precision": 0.887, "recall": 0.879, "f1_score": 0.883},
    {"name": "Random Forest (M2)", "type": "random_forest", "accuracy": 0.914, "precision": 0.911, "recall": 0.906, "f1_score": 0.908},
    {"name": "KNN (M3)", "type": "knn", "accuracy": 0.856, "precision": 0.849, "recall": 0.841, "f1_score": 0.845},
    {"name": "CNN+SVM (H1)", "type": "cnn_svm", "accuracy": 0.967, "precision": 0.965, "recall": 0.958, "f1_score": 0.962},
    {"name": "MobileNet+RF (H2)", "type": "transfer_rf", "accuracy": 0.948, "precision": 0.944, "recall": 0.939, "f1_score": 0.941},
]

DISEASES = ["Healthy", "Black_rot", "Esca", "Leaf_blight"]

DISEASE_FILENAMES = {
    "Healthy": ["hoja_sana_01.jpg", "hoja_sana_02.jpg", "hoja_sana_03.jpg", "vitis_verde_01.jpg", "parra_ok_01.jpg"],
    "Black_rot": ["black_rot_01.jpg", "podredumbre_01.jpg", "black_rot_02.jpg", "mancha_negra_01.jpg"],
    "Esca": ["esca_01.jpg", "esca_02.jpg", "enfermedad_madera_01.jpg", "apoplejia_01.jpg"],
    "Leaf_blight": ["leaf_blight_01.jpg", "tizon_01.jpg", "isariopsis_01.jpg", "mancha_hoja_01.jpg"],
}


def random_date(days_back: int) -> datetime:
    now = datetime.utcnow()
    past = now - timedelta(days=days_back)
    return past + timedelta(seconds=random.randint(0, int((now - past).total_seconds())))


def main(count: int = 50):
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
        for m in MODELS:
            db.add(ModelModel(**m))
        db.commit()
        print(f"✓ {len(MODELS)} modelos creados")
    else:
        print("→ Modelos ya existen, omitiendo")

    if db.query(DiagnosticModel).count() == 0:
        users = db.query(UserModel).all()
        for _ in range(count):
            user = random.choice(users)
            disease = random.choice(DISEASES)
            model = random.choice(MODELS)
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
                result=disease,
                confidence=confidence,
                model_used=model["name"],
                probabilities=json.dumps(probs),
                inference_time_ms=random.randint(150, 2500),
                analysis_type="consensus" if random.random() > 0.3 else "single",
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
        print(f"✓ {count} diagnósticos seed creados")
    else:
        print(f"→ Diagnósticos ya existen ({db.query(DiagnosticModel).count()}), omitiendo")

    db.close()
    print("✓ Seed completado")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=50, help="Número de diagnósticos seed")
    args = parser.parse_args()
    main(args.count)
