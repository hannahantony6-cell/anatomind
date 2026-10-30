from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent  # backend/


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BASE_DIR / ".env", extra="ignore")

    app_name: str = "Anatomind"
    database_url: str = f"sqlite:///{BASE_DIR / 'anatomind.db'}"

    secret_key: str = ""
    access_token_minutes: int = 60
    cookie_name: str = "anatomind_session"
    cookie_secure: bool = False
    cors_origins: str = "http://localhost:5173"

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2:3b"
    ollama_timeout_seconds: float = 240.0
    ollama_max_retries: int = 2
    ollama_num_ctx: int = 8192

    embedding_model: str = "BAAI/bge-small-en-v1.5"
    embedding_dim: int = 384
    retrieval_top_k: int = 6
    min_context_chars: int = 600
    quiz_generation_attempts: int = 4
    quiz_size: int = 5
    remediation_max_failed: int = 3

    pdf_path: str = str(BASE_DIR / "data" / "anatomy-and-physiology-2e_-_WEB.pdf")

    @field_validator("secret_key")
    @classmethod
    def _secret_strength(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError(
                "SECRET_KEY must be set (>= 32 chars). Generate one with: "
                'python -c "import secrets; print(secrets.token_urlsafe(48))" and put it in backend/.env'
            )
        return v

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
