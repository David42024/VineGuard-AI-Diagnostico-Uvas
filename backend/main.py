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

from backend.api import auth, diagnosis, models, pipeline, statistics, reports, users


def _check_alembic_revision():
    """Verify Alembic migrations are up to date. Fail loudly if not."""
    from alembic.config import Config as AlembicConfig
    from alembic.script import ScriptDirectory
    from alembic.runtime.migration import MigrationContext

    alembic_cfg = AlembicConfig(str(PROJECT_ROOT / "alembic.ini"))
    alembic_cfg.set_main_option("script_location", str(PROJECT_ROOT / "alembic"))
    alembic_cfg.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

    script = ScriptDirectory.from_config(alembic_cfg)
    head_rev = script.get_current_head()

    with engine.connect() as conn:
        mc = MigrationContext.configure(conn)
        current_rev = mc.get_current_revision()

    return current_rev, head_rev


def _run_alembic_upgrade():
    """Run alembic upgrade head."""
    from alembic.config import CommandLine as AlembicCommandLine
    alembic_cfg = str(PROJECT_ROOT / "alembic.ini")
    cmd = AlembicCommandLine()
    cmd.parser.prog = "alembic"
    cmd.run_cmd(AlembicConfig(alembic_cfg), ["upgrade", "head"])


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.STORAGE_DIR.mkdir(parents=True, exist_ok=True)

    # --- Alembic migration check ---
    try:
        current_rev, head_rev = _check_alembic_revision()
        if current_rev != head_rev:
            if settings.ENVIRONMENT == "development":
                print(f"[Alembic] DB at revision {current_rev}, head is {head_rev}. Auto-upgrading...")
                _run_alembic_upgrade()
                current_rev, head_rev = _check_alembic_revision()
                print(f"[Alembic] Now at revision {current_rev}")
            else:
                raise RuntimeError(
                    f"Database is at revision {current_rev} but expected {head_rev}. "
                    f"Run 'alembic upgrade head' before starting the server."
                )
        print(f"[Alembic] OK — revision {current_rev} (head)")
    except RuntimeError:
        raise
    except Exception as e:
        # Tables may not exist yet — init_db will create them, then Alembic can track
        print(f"[Alembic] Version check skipped: {e}")

    # --- SQLAlchemy create_all (safe — only creates missing tables) ---
    init_db()

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
