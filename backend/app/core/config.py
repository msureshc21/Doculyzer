"""
Application configuration settings.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )
    
    # API Settings
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "AI Paperwork Co-pilot"
    
    # Database Settings
    # Default to SQLite for development (no PostgreSQL required)
    # For production, set DATABASE_URL in .env to PostgreSQL connection string
    DATABASE_URL: str = "sqlite:///./paperwork_copilot.db"
    
    # File Storage Settings
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE: int = 10485760  # 10MB default
    
    # Security Settings
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30


settings = Settings()

