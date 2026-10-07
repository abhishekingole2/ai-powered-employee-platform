from abc import ABC, abstractmethod
import os

import httpx
from dotenv import load_dotenv


load_dotenv()


class LLMProvider(ABC):

    @abstractmethod
    def chat(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
    ) -> dict:
        pass


class OllamaProvider(LLMProvider):

    def __init__(self, model: str | None = None, base_url: str | None = None):
        self.model = model or os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
        self.base_url = base_url or os.getenv(
            "OLLAMA_BASE_URL",
            "http://127.0.0.1:11434",
        )

    def chat(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
    ) -> dict:

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
        }

        if tools:
            payload["tools"] = tools

        response = httpx.post(
            f"{self.base_url}/api/chat",
            json=payload,
            timeout=300,
        )

        response.raise_for_status()

        return response.json()
