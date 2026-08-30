from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    APP_NAME: str = "AI Recipe-to-Commerce Backend"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    PORT: int = 8000
    CONFIDENCE_THRESHOLD: float = 0.70

    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/recipe_commerce"

    JWT_SECRET: str = "default_secret_key_for_dev_only_change_in_production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_SECONDS: int = 3600

    SUPABASE_URL: str = "https://your-project-id.supabase.co"
    SUPABASE_KEY: str = "your-supabase-key"

    GEMINI_API_KEY: str = ""
    GOOGLE_API_KEY: str = ""

    VERTEX_PROJECT_ID: str = "your-gcp-project-id"
    VERTEX_LOCATION: str = "us-central1"
    VERTEX_MODEL_NAME: str = "gemini-1.5-flash"
    VERTEX_VISION_MODEL_NAME: str = "gemini-1.5-pro"

    CORS_ORIGINS: str = "*"

settings = Settings()

