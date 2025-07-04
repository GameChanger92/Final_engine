# src/llm/gemini_client.py
import os

# ── UNIT_TEST_MODE용 더미 ───────────────────────────────
if os.getenv("UNIT_TEST_MODE") == "1":

    class GeminiClient:  # type: ignore
        def __init__(self, *_, **__): ...
        def generate(self, prompt: str) -> str:
            # 600자 분량 · 주인공 첫 등장 · 액션·대사 포함
            return (
                '주인공 첫 등장. "대체 무슨 일이 벌어진 거지?" 그는 숨을 고르며 주위를 살폈다. '
                '빛나는 검이 허공을 가르며 적을 제압한다. "놈들이 돌아왔다!" 그녀가 외친다. '
                "타닥— 불꽃이 튀고, 발걸음이 돌바닥을 울린다. "
                "긴장과 설렘이 교차하는 가운데, 주인공은 한 걸음 내딛는다. "
                "머릿속엔 수많은 의문이 스쳐 지나가지만, 지금은 싸워야 할 때. "
                "팽팽한 공기가 주변을 감싸고, 관객의 숨소리마저 멎어 버린 듯하다. "
                "그의 첫 선택이 향후 운명을 결정짓게 될 것임을 누구도 모른다. "
                "이렇게 이야기는 시작된다…"
            )


# ── 실제 Vertex AI 호출용 ───────────────────────────────
else:
    from vertexai.language_models import TextGenerationModel

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
