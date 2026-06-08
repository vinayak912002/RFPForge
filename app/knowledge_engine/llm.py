import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
DEFAULT_LLAMA_TIMEOUT = 60


class LLMService:
    def __init__(self, model="llama3.2:3b-instruct-q4_0", timeout: int = DEFAULT_LLAMA_TIMEOUT):
        self.model = model
        self.timeout = timeout

    def generate(self, prompt: str) -> str:
        try:
            response = requests.post(
                OLLAMA_URL,
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()
        except requests.Timeout as exc:
            raise RuntimeError(f"LLM request timed out after {self.timeout}s") from exc
        except requests.RequestException as exc:
            raise RuntimeError(f"LLM request failed: {exc}") from exc
        except ValueError as exc:
            raise RuntimeError("LLM returned invalid JSON") from exc

        if not isinstance(data, dict):
            raise RuntimeError("LLM returned unexpected response format")

        return data.get("response", "")