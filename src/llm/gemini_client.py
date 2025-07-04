# src/llm/gemini_client.py
import os

# ── UNIT_TEST_MODE용 더미 ───────────────────────────────
if os.getenv("UNIT_TEST_MODE") == "1":

    class GeminiClient:  # type: ignore
        def __init__(self, *_, **__): ...
        def generate(self, prompt: str) -> str:
            # 600자 이상 · '주인공 첫 등장' 키워드 · 액션·대사 포함
            return (
                "주인공 첫 등장 그는 숨을 고르며 주위를 살폈다. "
                "[action] 빛나는 검이 허공을 가르며 적을 베었다. "
                '"놈들이 돌아왔다!" 그녀가 외쳤다. '
                "[action] 화염 기둥이 솟구치며 돌바닥을 뒤흔들었다. "
                '"이대로 물러설 순 없어!" 그가 이를 악물었다. '
                "긴장과 설렘이 교차하는 가운데, 주인공은 첫 선택을 한다. "
                "관중들의 숨소리조차 멎은 듯 고요한 순간, 심장이 요동쳤다. "
                "[action] 번개처럼 몸을 던져 동료를 지켜내고, "
                '"우리의 싸움은 지금부터야!" 힘찬 외침이 울려 퍼졌다. '
                "모닥불이 활활 타오르며 그림자를 길게 드리웠다. "
                "첫 번째 시련이 눈앞에 펼쳐졌지만, 그는 결코 물러서지 않을 터였다. "
                "[action] 검 끝이 빛을 머금고, 파열음과 함께 공기를 갈랐다. "
                '"끝까지 싸우자!" 동료들이 화답했고, 전장은 함성으로 가득 찼다. '
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
