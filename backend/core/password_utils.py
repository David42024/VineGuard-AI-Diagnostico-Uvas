"""Utilidades de contraseña puras (sin dependencias de FastAPI).

Este módulo solo depende de bcrypt y puede ser importado tanto desde
el entorno venv_ml (Streamlit) como desde venv_api (FastAPI) sin
arrastrar dependencias web.
"""

import bcrypt as _bcrypt

def hash_password(password: str) -> str:
    """Genera un hash bcrypt para la contraseña dada."""
    return _bcrypt.hashpw(password.encode("utf-8"), _bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica una contraseña contra su hash bcrypt."""
    try:
        return _bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except Exception:
        return False
