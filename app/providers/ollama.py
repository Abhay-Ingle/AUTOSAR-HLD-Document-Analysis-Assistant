import httpx


class OllamaLLM:
    """Minimal Ollama adapter; the endpoint is restricted to local hosts by settings."""

    def __init__(self, base_url: str, model: str, timeout: float = 120.0) -> None:
        self.base_url = base_url
        self.model = model
        self.timeout = timeout

    def generate(self, prompt: str) -> str:
        response = httpx.post(
            f"{self.base_url}/api/generate",
            json={"model": self.model, "prompt": prompt, "stream": False},
            timeout=self.timeout,
        )
        response.raise_for_status()
        payload = response.json()
        result = payload.get("response")
        if not isinstance(result, str) or not result.strip():
            raise RuntimeError("local LLM returned no response")
        return result

