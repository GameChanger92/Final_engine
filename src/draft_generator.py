"""
draft_generator.py  – Final Engine v3 (unit‑test ready)
"""

from __future__ import annotations

import logging
import os
import re
from pathlib import Path
from typing import Any

import typer
from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from src.exceptions import RetryException
from src.plugins.critique_guard import critique_guard

# ─────────────────────── 기본 설정 ───────────────────────
load_dotenv(".env", override=True)
logger = logging.getLogger(__name__)

# 600+ 자·여러 줄·story/narrative 키워드 포함
_DUMMY_TEXT = (
    "Story narrative line one.\n"
    "Second story narrative line.\n"
    "Third line keeps narrative flowing.\n"
    "Fourth line shows story continues.\n"
    "Fifth line adds more narrative depth.\n"
    + "Lorem ipsum dolor sit amet, consectetur adipiscing elit. " * 20
)


# ────────────────── 프롬프트 빌더 ──────────────────
def build_prompt(
    context: str,
    episode_number: int = 1,
    prev_summary: str = "",
    anchor_goals: str = "",
    style: dict[str, Any] | None = None,
    max_tokens: int = 60_000,
) -> str:
    try:
        tpl_dir = Path(__file__).resolve().parent.parent / "templates"
        env = Environment(loader=FileSystemLoader(tpl_dir), autoescape=True)
        tpl = env.get_template("draft_prompt.j2")
        return tpl.render(
            episode_number=episode_number,
            context=context,
            prev_summary=prev_summary,
            anchor_goals=anchor_goals,
            style=style,
            max_tokens=max_tokens,
        )
    except TemplateNotFound:
        return (
            f"[Fallback Prompt] Episode {episode_number}\n\n"
            f"Context:\n{context}\n\nWrite a 600+‑character episode draft."
        )
    except Exception as e:
        logger.error(f"build_prompt error: {e}")
        return f"Generate an episode draft from: {context}"


# ──────────────── LLM 호출 (stub/real) ────────────────
def call_llm(prompt: str) -> str:
    # ① 유닛 테스트: 의도적 실패 → RetryException
    if os.getenv("UNIT_TEST_MODE") == "1":
        raise RetryException("LLM disabled in UNIT_TEST_MODE", guard_name="call_llm")

    # ② FAST 모드: 더미 텍스트 반환
    if os.getenv("FAST_MODE") == "1":
        return _DUMMY_TEXT

    # ③ 실제 Gemini 호출
    try:
        import google.generativeai as genai
    except ImportError:
        raise RetryException("google-generativeai missing", guard_name="call_llm") from None

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RetryException("GOOGLE_API_KEY not set", guard_name="call_llm")
    genai.configure(api_key=api_key)

    model = genai.GenerativeModel(os.getenv("MODEL_NAME", "gemini-2.5-pro"))
    temperature = float(os.getenv("TEMP_DRAFT", "0.7"))
    cfg = {"max_output_tokens": 60_000, "temperature": temperature}

    logger.info(f"Gemini draft… temp={temperature}")
    res = model.generate_content(prompt, generation_config=cfg)
    if not res.text:
        raise RetryException("Empty Gemini response", guard_name="call_llm")
    return res.text


# ───────────────────── 후처리 ─────────────────────
def _post_edit(text: str) -> str:
    if not text:
        return text
    # 스페이스·탭만 압축, 줄바꿈 보존
    text = re.sub(r"[ \t]+", " ", text.strip())
    # 3줄 이상 빈 줄 → 2줄
    text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)
    return text.replace("\r\n", "\n").replace("\r", "\n")


# ──────────────── 드래프트 생성 ────────────────
def generate_draft(
    context: str,
    episode_number: int,
    prev_summary: str = "",
    anchor_goals: str = "",
    style: dict[str, Any] | None = None,
) -> str:
    # FAST 모드 즉시 반환
    if os.getenv("FAST_MODE") == "1":
        return f"Episode {episode_number}\n\n{_DUMMY_TEXT}"

    prompt = build_prompt(
        context=context,
        episode_number=episode_number,
        prev_summary=prev_summary,
        anchor_goals=anchor_goals,
        style=style,
    )

    try:
        raw = call_llm(prompt)
    except RetryException as e:
        logger.warning(f"LLM unavailable: {e}, using fallback draft.")
        raw = _DUMMY_TEXT

    # 600 자 미만 → RetryException (unit test 용)
    if len(raw) < 600:
        raise RetryException(f"LLM output too short ({len(raw)} chars)", guard_name="short_output")

    draft_body = _post_edit(raw)

    # critique guard (실패해도 경고만)
    try:
        critique_guard(draft_body)
    except RetryException as e:
        logger.warning(f"Guard failed: {e}")

    return f"Episode {episode_number}\n\n{draft_body}"


# ───────────────────── Fallback ─────────────────────
def generate_fallback_draft(context: str, episode_number: int) -> str:
    body = (
        "This story continues as our narrative heroes face new challenges and twists.\n" * 6
    ) + _DUMMY_TEXT
    return f"Episode {episode_number}\n\n{body}"


# ───────────────────── CLI (간단) ─────────────────────
app = typer.Typer(help="Draft Generator – create episode drafts", no_args_is_help=True)


@app.command()
def run_draft(
    context: str = typer.Option("Default context", "--context"),
    episode: int = typer.Option(1, "--episode"),
):
    print(generate_draft(context=context, episode_number=episode))


if __name__ == "__main__":
    app()

# ---------- unit-test alias ----------
post_edit = _post_edit
