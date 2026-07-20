from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    APP_NAME: str = "VineGuard AI API"
    VERSION: str = "1.0.0"
    API_PORT: int = 8000
    LOG_LEVEL: str = "INFO"

    # Security
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"

    # Database
    DATABASE_URL: str = f"sqlite:///{(BASE_DIR / 'data' / 'vinguard.db').as_posix()}"

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]
    CORS_ORIGINS_EXTRA: str = ""

    # Uploads
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024
    STORAGE_DIR: Path = BASE_DIR / "data"
    UPLOAD_DIR: Path = BASE_DIR / "data" / "uploads"

    # Environment
    ENVIRONMENT: str = "development"
    # Chatbot (Groq — LLM gratuito, ver https://console.groq.com/keys)
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.1-8b-instant"
    
    @property
    def cors_origins(self) -> list[str]:
        origins = list(self.CORS_ORIGINS)
        if self.CORS_ORIGINS_EXTRA:
            origins.extend([o.strip() for o in self.CORS_ORIGINS_EXTRA.split(",")])
        return origins


settings = Settings()
