import requests
from app.llm.config import OLLAMA_BASE_URL, MODEL_NAME, TIMEOUT


def generate_response(prompt: str) -> str:
    url = f"{OLLAMA_BASE_URL}/api/generate"

    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False
    }

    try:
        response = requests.post(url, json=payload, timeout=TIMEOUT)
        response.raise_for_status()

        data = response.json()
        return data.get("response", "")

    except Exception as e:
        return f"LLM Error: {str(e)}"