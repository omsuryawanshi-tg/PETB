"""
Application configuration using Pydantic Settings.
Loads from environment variables / .env file.
"""
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # --- Application ---
    APP_NAME: str = "PETB — Patient Engagement & Triage Bot"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False

    # --- Security ---
    SECRET_KEY: str = "petb-dev-secret-change-in-production-2026"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # --- Database ---
    DATABASE_URL: str = "sqlite:///./triage.db"

    # --- Ollama / LLM ---
    OLLAMA_MODEL: str = "qwen2.5:3b"
    OLLAMA_BASE_URL: str = "http://localhost:11434"

    # --- RAG ---
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    GUIDELINES_DIR: str = str(Path(__file__).resolve().parent.parent.parent / "data" / "guidelines")
    CHROMA_PERSIST_DIR: str = str(Path(__file__).resolve().parent.parent.parent / "data" / "chroma_db")

    # --- CORS ---
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


settings = Settings()
