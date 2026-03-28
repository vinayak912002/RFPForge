import requests

OLLAMA_URL = "http://localhost:11434/api/generate"


class LLMService:
    def __init__(self, model="llama3.2:3b-instruct-q4_0 "):
        self.model = model

    def generate(self, prompt: str) -> str:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False
            }
        )

        return response.json()["response"]