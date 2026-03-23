from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # App
    DEBUG: bool = False
    APP_NAME: str = "LLM Cost Monitor"

    # Database
    DATABASE_URL: str

    # Redis
    REDIS_URL: str

    # Encryption
    MASTER_ENCRYPTION_KEY: str

    # JWT RS256
    JWT_PRIVATE_KEY: str
    JWT_PUBLIC_KEY: str
    JWT_ALGORITHM: str = "RS256"
    JWT_EXPIRE_HOURS: int = 24

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    # Email notifications (Resend)
    RESEND_API_KEY: str = ""           # empty = notifications disabled
    NOTIFICATIONS_FROM_EMAIL: str = "alerts@llmcostmonitor.com"


settings = Settings()
