from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Logging
    LOG_LEVEL: str = "INFO"

    # Database
    DATABASE_URL: str
    DB_ECHO: bool = False
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20

    # Redis
    REDIS_URL: str
    REDIS_MAX_CONNECTIONS: int = 20

    # Docs configuration
    ENABLE_DOCS: bool = False

    # Security
    PUBLIC_KEY: str
    PRIVATE_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 150
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    class Config:
        env_file = ".env"


settings = Settings()
