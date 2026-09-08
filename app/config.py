import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    GEMINI_API_KEY: str = ""
    QDRANT_URL: str = ""
    QDRANT_API_KEY: str = ""
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""
    SQLITE_URL: str = "sqlite:///./app_data.db"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()