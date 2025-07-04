"""
GeminiClient
────────────
* UNIT_TEST_MODE=1  →  더미 응답(빠른 테스트)
* GOOGLE_API_KEY 가 있으면 → google-generativeai 실 호출
"""

import os

# ────────────────────────────────────────────────
# ① 테스트용 더미 클라이언트
# ────────────────────────────────────────────────
if os.getenv("UNIT_TEST_MODE") == "1":

    class GeminiClient:  # type: ignore
        def __init__(self, *_, **__): ...

        def generate(self, prompt: str, *_, **__) -> str:
            # Guard 통과용(≥600자·action·대사 포함)
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


# ────────────────────────────────────────────────
# ② 실 호출: google-generativeai
# ────────────────────────────────────────────────
else:
    import google.generativeai as genai

    class GeminiClient:
        def __init__(
            self,
            model_name: str = os.getenv("MODEL_NAME", "gemini-2.5-pro"),
            max_tokens: int = int(os.getenv("MAX_TOKENS", 60000)),
            temperature: float = float(os.getenv("TEMP_DRAFT", 0.7)),
        ):
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                raise ValueError("GOOGLE_API_KEY env var not set")

            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel(model_name)
            self.max_tokens = max_tokens
            self.temperature = temperature

        # ────────────────────────────────────────
        # 초안 생성
        # ────────────────────────────────────────
        def generate(self, prompt: str, episode_number: int = 0) -> str:
            try:
                # 1) 스트리밍 호출
                stream = self.model.generate_content(
                    prompt,
                    stream=True,
                    generation_config={
                        "max_output_tokens": self.max_tokens,
                        "temperature": self.temperature,
                    },
                    # 가장 자주 막히는 두 카테고리만 해제
                    safety_settings=[
                        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
                    ],
                )

                # 2) chunk를 모아 완성
                chunks: list[str] = []
                for chunk in stream:
                    if chunk.candidates and chunk.candidates[0].content.parts:
                        # 모든 parts를 처리 (한 chunk에 여러 part가 있을 수 있음)
                        for part in chunk.candidates[0].content.parts:
                            if getattr(part, "text", None):
                                chunks.append(part.text)

                full_text = "".join(chunks).strip()
                if not full_text:
                    raise ValueError("Empty response from Gemini")
                return full_text

            except Exception as e:
                # 3) 어떤 이유로든 실패 시 더미 초안으로 대체
                print(f"⚠️  Gemini blocked or errored: {e} – using fallback draft")
                from src.draft_generator import generate_draft

                return generate_draft("", episode_number)
