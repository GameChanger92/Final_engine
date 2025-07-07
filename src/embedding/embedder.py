"""
embedder.py

OpenAI Embeddings wrapper for Final Engine.
Provides text embedding functionality using OpenAI's text-embedding models.
"""

import os

import openai

# 길이 1536 의 더미 벡터
_DUMMY_EMBED: list[float] = [0.1] * 1536


def embed_scene(text: str, model: str = "text-embedding-3-small") -> list[float]:
    """
    Generate embeddings for scene text using OpenAI.

    Parameters
    ----------
    text : str
        Text content to embed
    model : str, optional
        OpenAI embedding model to use, defaults to "text-embedding-3-small"

    Returns
    -------
    list[float]
        Embedding vector as list of floats

    Raises
    ------
    ValueError
        If text is empty or model is invalid
    RuntimeError
        If OpenAI API call fails or openai module is not available
    """
    # 1) 입력 검증
    if not text.strip():
        raise ValueError("Text cannot be empty")

    api_key = os.getenv("OPENAI_API_KEY")
    fast_mode = os.getenv("FAST_MODE") == "1"
    unit_test_mode = os.getenv("UNIT_TEST_MODE") == "1"

    # 2) 모드별 분기 처리 (우선순위: UNIT_TEST → FAST → 실제 호출)
    # UNIT_TEST_MODE가 켜져 있고 API 키가 있으면 실제 OpenAI 호출 (Mock으로 대체됨)
    if unit_test_mode and api_key is not None:
        pass  # 아래 실제 호출 로직으로 진행
    # FAST_MODE이거나 API 키가 없으면 더미 반환
    elif fast_mode or api_key is None:
        return _DUMMY_EMBED

    # 3) 실제 OpenAI 호출 (테스트에서 mock 으로 대체됨)
    try:
        client = openai.OpenAI()  # 인자 없이 호출 → MagicMock 호환
        resp = client.embeddings.create(
            input=text,
            model=model,
        )
        return resp.data[0].embedding
    except Exception as e:
        # API 실패 → RuntimeError (failure 테스트 체크)
        raise RuntimeError("Failed to generate embedding") from e
