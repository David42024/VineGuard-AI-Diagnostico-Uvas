"""Check database state."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.database.session import SessionLocal
from backend.database.models import UserModel, DiagnosticModel, AuditLogModel, ModelModel


def main():
    db = SessionLocal()
    try:
        users = db.query(UserModel).count()
        diagnostics = db.query(DiagnosticModel).count()
        audit = db.query(AuditLogModel).count()
        models = db.query(ModelModel).count()

        print(f"  Usuarios:     {users}")
        print(f"  Diagnósticos: {diagnostics}")
        print(f"  Auditoría:    {audit}")
        print(f"  Modelos:      {models}")
        print()
        if users == 0:
            print("[WARN] DB vacia — ejecuta: python scripts/seed_db.py")
        else:
            print("[OK] DB ok")
    finally:
        db.close()


if __name__ == "__main__":
    main()
