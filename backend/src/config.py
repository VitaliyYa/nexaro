from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Supabase Configuration
    SUPABASE_URL: str = "http://127.0.0.1:54321"
    SUPABASE_PUBLISHABLE_KEY: str = "sb_publishable_dev_key"
    SUPABASE_SECRET_KEY: str = "sb_secret_dev_key"
    SUPABASE_JWKS_URL: str | None = None
    SUPABASE_JWT_SECRET: str | None = None
    SUPABASE_JWT_ALGORITHM: str = "HS256"

    # MQTT Broker Configuration
    MQTT_BROKER_HOST: str = "localhost"
    MQTT_BROKER_PORT: int = 8883
    MQTT_TLS_ENABLED: bool = True
    MQTT_CA_CERT_PATH: str | None = None

    MQTT_CLIENT_CERT_PATH: str | None = None
    MQTT_CLIENT_KEY_PATH: str | None = None
    MQTT_WORKER_USERNAME: str = "backend_worker"
    MQTT_WORKER_PASSWORD: str = "secret_backend_worker_pass"
    MQTT_KEEPALIVE: int = 60

    # Security & Encryption
    # 32-byte Fernet key (e.g. Fernet.generate_key().decode())
    PIN_ENCRYPTION_KEY: str = "k5M7j0v9y9mE2q_u2bW2Zg3d1K4t6F8s0A2b4C6d8E0="

    # CORS
    CORS_ORIGINS: list[str] = ["*"]


@lru_cache
def get_settings() -> Settings:
    return Settings()
