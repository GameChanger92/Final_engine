# src/llm/gemini_client.py
import os

from vertexai.language_models import TextGenerationModel  # Vertex AI SDK


class GeminiClient:
    def __init__(
        self,
        model_name: str = os.getenv("MODEL_NAME", "gemini-2.5-pro"),
        max_tokens: int = 60000,
        temperature: float = float(os.getenv("TEMP_DRAFT", 0.7)),
    ):
        self.model = TextGenerationModel.from_pretrained(model_name)
        self.max_tokens = max_tokens
        self.temperature = temperature

    def generate(self, prompt: str) -> str:
        response = self.model.predict(
            prompt,
            max_output_tokens=self.max_tokens,
            temperature=self.temperature,
        )
        return response.text
