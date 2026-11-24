from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Career Compass API"
    API_V1_PREFIX: str = "/api/v1"
    API_BASE_URL: str = ""
    DEBUG: bool = True

    DATABASE_URL: str = ""
    CORS_ORIGINS: str = ""

    GEMINI_API_KEY: str = ""
    GROQ_API_KEY: str = ""

    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""

    @property
    def cors_origins(self) -> list[str]:
        """Return the comma-separated frontend origins configured for CORS."""
        return [
            origin.strip()
            for origin in self.CORS_ORIGINS.split(",")
            if origin.strip()
        ]

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[2] / ".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()