from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    APP_NAME: str = "E-DÉFENCE IA Analyse États Financiers"
    VERSION: str = "4.0.0"
    DEBUG: bool = False
    API_PREFIX: str = "/api/v1"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://edefence:edefence@localhost:5432/analyse_financiere"
    DATABASE_SYNC_URL: str = "postgresql://edefence:edefence@localhost:5432/analyse_financiere"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Security
    SECRET_KEY: str = "CHANGE_THIS_SECRET_KEY_IN_PRODUCTION_256_BITS"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    MFA_ISSUER: str = "E-DEFENCE SaaS"

    # Encryption
    AES_KEY: str = "CHANGE_THIS_AES_KEY_32_BYTES_PROD"

    # CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "https://app.edefence.tech"]

    # Claude / Anthropic
    ANTHROPIC_API_KEY: str = ""

    # OCR (optional, configure one)
    GOOGLE_CLOUD_PROJECT: str = ""
    AWS_REGION: str = "eu-west-1"

    # File upload
    MAX_UPLOAD_SIZE_MB: int = 50
    UPLOAD_DIR: str = "/tmp/edefence_uploads"

    # Email / SMTP
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = "noreply@edefence.tech"
    SMTP_USE_TLS: bool = False
    SMTP_USE_STARTTLS: bool = True
    FRONTEND_URL: str = "http://localhost:3000"

    # Password reset
    RESET_TOKEN_EXPIRE_MINUTES: int = 30

    # CinetPay
    CINETPAY_API_KEY: str = ""
    CINETPAY_SITE_ID: str = ""
    BACKEND_URL: str = "http://localhost:8000"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
