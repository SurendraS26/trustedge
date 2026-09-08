import os
import ollama


class OllamaClient:
    def __init__(self, model: str | None = None):
        self.model = model or os.environ.get("OLLAMA_MODEL")
        if not self.model:
            raise RuntimeError(
                "No model configured. Set OLLAMA_MODEL in .env "
                "(manual model choice) and restart c1."
            )
        self.client = ollama.Client(host="http://127.0.0.1:11434")

    def chat(self, messages: list[dict], tools: list[dict] | None = None) -> dict:
        """
        Sends a chat request to the configured model.
        `tools` follows Ollama's tool-calling schema, if the model supports it.
        Returns the raw response dict from Ollama.
        """
        response = self.client.chat(
            model=self.model,
            messages=messages,
            tools=tools or [],
        )
        return response

    def list_local_models(self) -> list[str]:
        """Returns model tags currently pulled into this Ollama instance."""
        models = self.client.list()
        return [m["name"] for m in models.get("models", [])]
