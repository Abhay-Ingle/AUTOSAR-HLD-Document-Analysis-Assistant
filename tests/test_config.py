import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_local_ollama_url_is_accepted() -> None:
    settings = Settings(ollama_base_url="http://localhost:11434")
    assert settings.ollama_base_url == "http://localhost:11434"


def test_external_ollama_url_is_rejected() -> None:
    with pytest.raises(ValidationError, match="local/private"):
        Settings(ollama_base_url="https://example.com")

