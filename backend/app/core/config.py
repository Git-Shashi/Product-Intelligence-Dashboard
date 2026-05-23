from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/product_dashboard"
    cors_origin: str = "http://localhost:5173"
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
