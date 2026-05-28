import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Application settings and configurations.
    Uses Pydantic Settings to automatically read variables from environment 
    or a local .env file.
    """
    # API configuration
    gemini_api_key: str = ""

    # Security configuration for JWT authentication
    secret_key: str = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # Database configuration
    database_url: str = "sqlite:///./interview_coach.db"

    # Server configuration
    host: str = "127.0.0.1"
    port: int = 8000
    log_level: str = "info"

    # Uploads configuration
    upload_dir: str = "backend/app/uploads"
    max_upload_size: int = 5 * 1024 * 1024  # 5MB in bytes

    # Automatically load environment variables from the .env file.
    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

# Instantiate settings to be imported across modules
settings = Settings()
