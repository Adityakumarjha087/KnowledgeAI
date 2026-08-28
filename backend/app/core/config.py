from typing import List, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # --- Application Configuration ---
    APP_NAME: str = "Enterprise AI Knowledge Assistant"
    APP_ENV: str = "production"
    SECRET_KEY: str

    # --- CORS: set CORS_ORIGINS to comma-separated list of allowed origins ---
    # e.g. "https://your-app.vercel.app,https://your-custom-domain.com"
    CORS_ORIGINS: str = "http://localhost:3000"

    # --- Database & Caching ---
    DATABASE_URL: str
    REDIS_URL: str = "redis://localhost:6379/0"

    # --- Authentication ---
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # --- LLM Provider ---
    LLM_PROVIDER: str = "openai"
    LLM_API_KEY: str = "your_openai_api_key_here"
    LLM_API_BASE: str = "https://api.openai.com/v1"
    LLM_MODEL: str = "gpt-4o-mini"

    # --- Embedding Provider ---
    EMBEDDING_PROVIDER: str = "openai"
    EMBEDDING_API_KEY: Optional[str] = None
    EMBEDDING_API_BASE: str = "https://api.openai.com/v1"
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDING_DIMENSION: int = 1536

    # --- Reranking Provider ---
    RERANK_PROVIDER: str = "mock"
    RERANK_API_KEY: Optional[str] = None
    RERANK_MODEL: str = "rerank-english-v3.0"

    # --- Storage Configuration ---
    STORAGE_PROVIDER: str = "local"
    STORAGE_BUCKET: str = "enterprise-rag-docs"
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_ENDPOINT_URL: Optional[str] = None
    AWS_REGION: str = "us-east-1"

    # --- Document Ingestion Config ---
    CHUNK_SIZE: int = 800
    CHUNK_OVERLAP: int = 150
    MAX_UPLOAD_SIZE_MB: int = 10
    ALLOWED_EXTENSIONS: str = "pdf,docx,txt,md"

    # --- Rate Limiting ---
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 60

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_url(cls, v: Optional[str]) -> str:
        if not v:
            raise ValueError("DATABASE_URL cannot be empty")
        return v

    @property
    def allowed_extensions_list(self) -> List[str]:
        return [ext.strip().lower() for ext in self.ALLOWED_EXTENSIONS.split(",")]

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


# Global settings instance
settings = Settings()
