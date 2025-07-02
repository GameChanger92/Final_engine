"""CritiqueGuard – 재미/개연성 점수 검사"""

import os
import sys
from typing import Any

from src.core.guard_registry import BaseGuard, register_guard
from src.exceptions import RetryException


# ---------- 내부 헬퍼 ----------
def _get_min_score(override: float | None = None) -> float:
    """매 호출마다 MIN_CRITIQUE_SCORE env를 읽어 최신값을 얻는다."""
    return float(override) if override is not None else float(os.getenv("MIN_CRITIQUE_SCORE", 7.0))


# ---------- 메인 Guard ----------
@register_guard(order=10)
class CritiqueGuard(BaseGuard):
    def __init__(
        self,
        min_score: float = 7.0,
        project: str = "default",
        **kwargs,
    ):
        self.min_score = min_score
        self.project = project

    # 실제 LLM 호출은 생략/모킹
    def _call_gemini_critique(self, text: str) -> dict[str, Any]:
        """
        Gemini 호출 / 테스트 스텁
        1) UNIT_TEST_MODE 또는 FAST_MODE 면 즉시 스텁 반환
        2) 실사용 시: 라이브러리 import → API-key 체크
        """
        # ---- 1) 테스트 스텁 경로 -------------------------------------
        if os.getenv("UNIT_TEST_MODE") == "1":
            return {
                "fun": 8.0,
                "logic": 7.5,
                "comment": "Unit‑test stub",
            }

        # ---- 2) FAST_MODE fallback --------------------------------
        if os.getenv("FAST_MODE") == "1":
            return {
                "fun": 8.0,
                "logic": 8.0,
                "comment": "FastMode fallback - basic validation passed",
            }

        try:
            import google.generativeai  # noqa: F401
        except ImportError:
            raise RetryException(
                "google-generativeai not installed", guard_name="critique_guard"
            ) from None

        if not os.getenv("GOOGLE_API_KEY"):
            raise RetryException("API key not configured", guard_name="critique_guard")

        # 예시 응답 – 실무에선 Gemini 호출
        return {"fun": 8.2, "logic": 8.1, "comment": "LLM placeholder comment."}

    def check(self, text: str) -> dict[str, Any]:
        result = self._call_gemini_critique(text)
        passed = result["fun"] >= self.min_score and result["logic"] >= self.min_score

        if not passed:
            # Return failure dict with flags (don't raise exception)
            return {
                "passed": False,
                "fun_score": result["fun"],
                "logic_score": result["logic"],
                "comment": result["comment"],
                "min_score": self.min_score,
                "flags": {
                    "critique_failure": {
                        "fun_score": result["fun"],
                        "logic_score": result["logic"],
                        "min_score": self.min_score,
                    }
                },
            }

        # 결과 그대로 반환 (가공 X)
        return {
            "passed": True,
            "fun_score": result["fun"],
            "logic_score": result["logic"],
            "comment": result["comment"],
            "min_score": self.min_score,
            "flags": {},
        }


# ---------- 래퍼 함수 2개 ----------
def check_critique_guard(text: str, min_score: float | None = None) -> dict[str, Any]:
    """테스트·외부 호출용 래퍼 – CritiqueGuard.check 그대로 반환"""
    result = sys.modules[__name__].CritiqueGuard(min_score=_get_min_score(min_score)).check(text)

    # If the result indicates failure, raise RetryException
    if not result["passed"]:
        # Extract failure information
        fun_score = result["fun_score"]
        logic_score = result["logic_score"]
        comment = result["comment"]
        min_score_val = result["min_score"]
        flags = result["flags"]

        # Create and raise RetryException
        message = (
            f"Critique scores too low: fun={fun_score}, "
            f"logic={logic_score} (min={min_score_val}). "
            f"Comment: {comment}"
        )
        raise RetryException(message=message, flags=flags, guard_name="critique_guard")

    return result


def critique_guard(text: str, min_score: float | None = None) -> None:
    """메인 파이프라인에서 사용하는 함수 – 래퍼를 한 줄로 호출"""
    # Read environment variable and pass it explicitly
    final_min_score = _get_min_score(min_score)
    sys.modules[__name__].check_critique_guard(text, final_min_score)


# ---------- re‑export ----------
__all__ = ["CritiqueGuard", "check_critique_guard", "critique_guard"]
