"""Drop and recreate all tables."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.database.base import Base
from backend.database.session import engine
from backend.database import models  # noqa: F401


def main():
    Base.metadata.drop_all(bind=engine)
    print("✓ Tablas eliminadas")
    Base.metadata.create_all(bind=engine)
    print("✓ Tablas recreadas")
    print(f"  DB: {engine.url}")


if __name__ == "__main__":
    main()
