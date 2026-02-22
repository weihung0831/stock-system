"""Application configuration using pydantic-settings."""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    DATABASE_URL: str
    FINMIND_TOKEN: str
    LLM_API_KEY: str
    LLM_BASE_URL: str = "https://api.apertis.ai/v1"
    LLM_MODEL: str = "gemini-2.5-pro"
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 1440
    CORS_ORIGINS: str = "http://localhost:5173"

    model_config = {
        "env_file": ".env"
    }

    @property
    def cors_origins_list(self) -> list[str]:
        """Convert CORS_ORIGINS string to list."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]


# Global settings instance
try:
    settings = Settings()
except Exception:
    # Allow loading in test environment
    settings = None
