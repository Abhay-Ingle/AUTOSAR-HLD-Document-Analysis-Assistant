from functools import lru_cache
from ipaddress import ip_address
from urllib.parse import urlparse

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1", "ollama", "chroma"}


def _validate_local_url(value: str) -> str:
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("provider URL must be an absolute HTTP(S) URL")
    host = parsed.hostname.lower()
    is_ip = False
    try:
        is_ip = ip_address(host).is_loopback
    except ValueError:
        pass
    if host not in _LOCAL_HOSTS and not is_ip:
        raise ValueError("provider URL must point to a local/private service")
    return value.rstrip("/")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="", extra="ignore")

    app_env: str = "development"
    database_url: str = "sqlite:///./data/autosar.db"
    api_host: str = "0.0.0.0"
    api_port: int = Field(default=8000, ge=1, le=65535)
    log_level: str = "INFO"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1:8b"
    embedding_provider: str = "sentence-transformers"
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    chroma_host: str = "localhost"
    chroma_port: int = Field(default=8000, ge=1, le=65535)
    chroma_collection: str = "autosar_hld_chunks"
    app_data_dir: str = "./data"
    max_upload_mb: int = Field(default=512, ge=1, le=4096)

    @field_validator("ollama_base_url")
    @classmethod
    def validate_ollama_base_url(cls, value: str) -> str:
        return _validate_local_url(value)


@lru_cache
def get_settings() -> Settings:
    return Settings()
