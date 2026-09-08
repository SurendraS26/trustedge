import os
import ollama


class OllamaClient:
    def __init__(self, model: str | None = None):
        self.model = model or os.environ.get("OLLAMA_MODEL")
        if not self.model:
            raise RuntimeError("No model configured. Set OLLAMA_MODEL in .env and restart c1.")
        self.client = ollama.Client(host="http://127.0.0.1:11434")

    def chat(self, messages: list[dict], tools: list[dict] | None = None) -> dict:
        return self.client.chat(model=self.model, messages=messages, tools=tools or [])

    def list_local_models(self) -> list[str]:
        models = self.client.list()
        return [m["name"] for m in models.get("models", [])]
