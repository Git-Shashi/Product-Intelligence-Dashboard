from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/product_dashboard"

    @field_validator("database_url", mode="before")
    @classmethod
    def fix_db_url(cls, v: str) -> str:
        # Render provides postgres:// — SQLAlchemy asyncpg requires postgresql+asyncpg://
        if v.startswith("postgres://"):
            v = "postgresql+asyncpg://" + v[len("postgres://"):]
        elif v.startswith("postgresql://") and "+asyncpg" not in v:
            v = "postgresql+asyncpg://" + v[len("postgresql://"):]
        return v
    cors_origin: str = "http://localhost:5173"
    # Comma-separated extra origins (e.g. Vercel preview URLs)
    cors_extra_origins: str = ""
    extraction_provider: str = "ocr"  # "ocr" | "mock"

    # Optional SMTP — no-op if unset
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = ""

    # Upload storage
    upload_dir: str = "/tmp/uploads"


settings = Settings()
