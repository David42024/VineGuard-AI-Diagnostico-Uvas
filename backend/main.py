import sys
import logging
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.core.config import settings
from backend.database.database import init_db
from backend.database.session import SessionLocal, engine

from backend.api import auth, diagnosis, models, pipeline, statistics, reports, users, chatbot


def _alembic_config():
    from alembic.config import Config as AlembicConfig
    cfg = AlembicConfig(str(PROJECT_ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(PROJECT_ROOT / "alembic"))
    cfg.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
    return cfg


def _check_alembic_revision():
    """Verify Alembic migrations are up to date."""
    from alembic.script import ScriptDirectory
    from alembic.runtime.migration import MigrationContext

    script = ScriptDirectory.from_config(_alembic_config())
    head_rev = script.get_current_head()

    with engine.connect() as conn:
        mc = MigrationContext.configure(conn)
        current_rev = mc.get_current_revision()

    return current_rev, head_rev


def _run_alembic_upgrade():
    """Run alembic upgrade head."""
    from alembic import command
    command.upgrade(_alembic_config(), "head")


def _stamp_alembic_head():
    """Mark the DB as at head revision without running migrations.

    Necesario cuando el esquema ya fue creado por `create_all` (init_db) y por
    tanto las migraciones ya no se pueden aplicar (tablas existentes).
    """
    from alembic import command
    command.stamp(_alembic_config(), "head")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.STORAGE_DIR.mkdir(parents=True, exist_ok=True)

    # --- Alembic migration check ---
    try:
        current_rev, head_rev = _check_alembic_revision()
        if current_rev != head_rev:
            if current_rev is None:
                # DB nueva sin historial de migraciones: el esquema ya lo creó
                # create_all (init_db), así que sólo marcamos la revisión head.
                print("[Alembic] DB nueva (sin revisiones). Marcando head...")
                _stamp_alembic_head()
                current_rev = head_rev
            elif settings.ENVIRONMENT == "development":
                print(f"[Alembic] DB at revision {current_rev}, head is {head_rev}. Auto-upgrading...")
                _run_alembic_upgrade()
                current_rev, head_rev = _check_alembic_revision()
                print(f"[Alembic] Now at revision {current_rev}")
            else:
                # En producción no bloqueamos: create_all ya garantiza el esquema.
                print(
                    f"[Alembic] WARN: DB en revisión {current_rev}, head es {head_rev}. "
                    f"Continuando (init_db asegura el esquema)."
                )
        print(f"[Alembic] OK — revision {current_rev} (head)")
    except RuntimeError:
        raise
    except Exception as e:
        # Tables may not exist yet — init_db will create them, then Alembic can track
        print(f"[Alembic] Version check skipped: {e}")

    # --- SQLAlchemy create_all (safe — only creates missing tables) ---
    init_db()

    # --- Auto-seed de usuarios por defecto (DB efímera en Render) ---
    if settings.AUTO_SEED_USERS:
        from backend.core.security import hash_password
        from backend.database.models import UserModel
        db = SessionLocal()
        try:
            if db.query(UserModel).count() == 0:
                default_users = [
                    {"name": "Administrador", "username": "admin", "password": "admin123", "role": "admin"},
                    {"name": "Usuario", "username": "usuario", "password": "12345", "role": "client"},
                ]
                for u in default_users:
                    db.add(UserModel(
                        name=u["name"],
                        username=u["username"],
                        password_hash=hash_password(u["password"]),
                        role=u["role"],
                    ))
                db.commit()
                print("[Startup] Usuarios por defecto creados (admin/admin123, usuario/12345)")
        finally:
            db.close()

    # --- Startup banner via SQLAlchemy ---
    try:
        from backend.database.models import UserModel, DiagnosticModel, ModelModel
        db = SessionLocal()
        u_count = db.query(UserModel).count()
        d_count = db.query(DiagnosticModel).count()
        m_count = db.query(ModelModel).count()
        db.close()
        print(f"""
╔══════════════════════════════════════════╗
║        VineGuard AI — Backend            ║
╠══════════════════════════════════════════╣
║  DB    : data/vinguard.db (SQLite)       ║
║  Users : {u_count:<3}                                  ║
║  Diags : {d_count:<3}                                  ║
║  Models: {m_count:<3}                                  ║
║  Port  : {settings.API_PORT:<3}                                 ║
╚══════════════════════════════════════════╝
        """)
    except Exception as e:
        print(f"[Startup] Banner skipped: {e}")

    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(diagnosis.router)
app.include_router(models.router)
app.include_router(pipeline.router)
app.include_router(statistics.router)
app.include_router(reports.router)
app.include_router(users.router)
app.include_router(chatbot.router)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error_code": f"HTTP_{exc.status_code}",
            "message": exc.detail,
            "details": None,
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "error_code": "INTERNAL_ERROR",
            "message": "Error interno del servidor",
            "details": str(exc) if settings.ENVIRONMENT == "development" else None,
        },
    )


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
    }
