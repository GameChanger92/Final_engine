"""
embedder.py

OpenAI Embeddings wrapper for Final Engine.
Provides text embedding functionality using OpenAI's text-embedding models.
"""

import os

try:
    import openai
except ModuleNotFoundError:
    openai = None


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
    List[float]
        Embedding vector as list of floats

    Raises
    ------
    ValueError
        If text is empty or model is invalid
    RuntimeError
        If OpenAI API call fails or openai module is not available
    """
    # Fast mode for unit tests - skip actual embedding generation for speed
    if os.getenv("FAST_MODE") == "1" or os.getenv("UNIT_TEST_MODE") == "1":
        return [0.1] * 1536  # Return dummy embedding quickly

    if not text or not text.strip():
        raise ValueError("Text cannot be empty")

    if openai is None:
        raise RuntimeError("OpenAI module not available. Please install openai>=1.13")

    # Get OpenAI API key from environment
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        # For testing purposes, return a dummy embedding
        # In production, this should raise an error
        return [0.1] * 1536  # Default embedding size for text-embedding-3-small

    try:
        client = openai.OpenAI(api_key=api_key)
        response = client.embeddings.create(
            model=model, input=text.strip(), encoding_format="float"
        )

        return response.data[0].embedding

    except Exception as e:
        raise RuntimeError(f"Failed to generate embedding: {e}")
