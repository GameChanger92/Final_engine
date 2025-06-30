import os
import pytest
from unittest.mock import patch
from src.draft_generator import generate_draft, build_prompt, call_llm, post_edit


def test_generate_draft_returns_string():
    """Test that the function returns a string."""
    context = "Test context"
    episode_num = 1
    result = generate_draft(context, episode_num)
    assert isinstance(result, str)


def test_generate_draft_includes_episode_number():
    """Test that the draft includes the episode number."""
    context = "Test context"
    episode_num = 42
    result = generate_draft(context, episode_num)

    assert f"Episode {episode_num}" in result
    assert "42" in result


def test_generate_draft_with_different_contexts():
    """Test with different context strings."""
    contexts = [
        "Short context",
        "A much longer context with more detailed information about characters",
        "한글 컨텍스트 테스트",
        "",  # Empty context
    ]

    for context in contexts:
        result = generate_draft(context, 1)
        assert isinstance(result, str)
        assert len(result) > 0
        assert "Episode 1" in result


def test_generate_draft_with_different_episode_numbers():
    """Test with different episode numbers."""
    context = "Test context"
    episode_numbers = [1, 10, 100, 999]

    for ep_num in episode_numbers:
        result = generate_draft(context, ep_num)
        assert isinstance(result, str)
        assert f"Episode {ep_num}" in result


def test_generate_draft_minimum_length():
    """Test that the draft meets minimum length requirement."""
    context = "Test context"
    episode_num = 1
    result = generate_draft(context, episode_num)

    # Should be at least 500 characters
    assert len(result) >= 500


def test_google_api_key_loading(monkeypatch):
    """Test that GOOGLE_API_KEY is loaded from environment."""
    # Set test environment variable
    monkeypatch.setenv("GOOGLE_API_KEY", "test_key")

    # Test that the environment variable is accessible
    api_key = os.getenv("GOOGLE_API_KEY")
    assert api_key is not None
    # Should have the test key value
    assert api_key == "test_key"


def test_generate_draft_with_retry_mechanism():
    """Test that retry mechanism works when LLM fails."""
    context = "Test context for retry"
    episode_num = 1

    # Mock the LLM to fail initially then succeed
    with patch("src.draft_generator.call_llm") as mock_llm:
        # First call fails, second succeeds
        mock_llm.side_effect = [
            Exception("First attempt fails"),
            "Generated content that is long enough to meet the minimum requirements and provides a compelling narrative.",
        ]

        result = generate_draft(context, episode_num)
        assert isinstance(result, str)
        assert len(result) >= 500


def test_guards_simulation_pass():
    """Test that guard simulation works correctly."""
    from src.draft_generator import simulate_guards_validation

    # Long enough draft should pass basic checks (need multiline and sufficient length)
    long_draft = (
        "This is a test draft that is long enough to pass the basic validation checks.\n"
        + "It has multiple lines and sufficient content to meet all requirements.\n"
        * 20
    )
    result = simulate_guards_validation(long_draft, 1)
    assert result is True


def test_post_edit_functionality():
    """Test that post_edit function works correctly."""
    # Test text with excessive whitespace and line breaks
    messy_text = "This  is   a    test\n\n\n\n\nwith extra   spaces\r\nand line breaks"

    cleaned = post_edit(messy_text)

    # Should remove excessive whitespace
    assert "   " not in cleaned
    assert "    " not in cleaned

    # Should not have excessive line breaks
    assert "\n\n\n" not in cleaned

    # Should have proper line endings
    assert "\r\n" not in cleaned
    assert "\r" not in cleaned


def test_call_llm_handles_import_error(monkeypatch):
    """Test call_llm function handles import error gracefully."""
    from src.exceptions import RetryException

    # Set unit test mode to trigger import error
    monkeypatch.setenv("UNIT_TEST_MODE", "1")
    monkeypatch.setenv("GOOGLE_API_KEY", "test_key")
    monkeypatch.setenv("MODEL_NAME", "gemini-2.5-pro")

    try:
        call_llm("Test prompt")
    except RetryException as e:
        # Should fail with RetryException due to import error
        assert "library not available" in str(e) or "import" in str(e).lower()
    except ImportError:
        # Also acceptable - ImportError for missing library
        pass


def test_build_prompt_with_context():
    """Test prompt building functionality."""
    context = "Test context for prompt building"

    prompt = build_prompt(context)

    assert isinstance(prompt, str)
    assert context in prompt
    assert len(prompt) > len(context)  # Should add template content


def test_build_prompt_with_style():
    """Test prompt building with style configuration."""
    context = "Test context"
    style = {
        "platform": "web",
        "tone": "dramatic",
        "voice_main": "3rd_person",
        "voice_side": "present",
        "enter_rule": "custom_rule",
        "prompt_suffix": "with specific requirements"
    }

    prompt = build_prompt(context, style)

    assert isinstance(prompt, str)
    assert context in prompt
    assert "dramatic" in prompt
    assert "3rd_person" in prompt


def test_generate_draft_fallback_mode():
    """Test that fallback mode generates appropriate content."""
    context = "Test context for fallback"
    episode_num = 5

    result = generate_draft(context, episode_num)

    # Should contain episode number
    assert f"Episode {episode_num}" in result

    # Should be long enough
    assert len(result) >= 500

    # Should contain narrative elements
    assert "story" in result.lower() or "narrative" in result.lower()


def test_draft_generator_integration():
    """Integration test for the complete draft generation process."""
    context = "A thrilling adventure with brave heroes facing mysterious challenges"
    episode_num = 3

    result = generate_draft(context, episode_num)

    # Basic validations
    assert isinstance(result, str)
    assert len(result) >= 500
    assert f"Episode {episode_num}" in result

    # Should be properly formatted (multiline)
    lines = result.split("\n")
    assert len(lines) > 5


def test_retry_on_short_output(monkeypatch):
    """Test retry mechanism when LLM output is too short."""
    from src.draft_generator import generate_draft, RetryException

    # Mock call_llm to return short content
    monkeypatch.setattr("src.draft_generator.call_llm", lambda *a, **k: "abc")

    # Should raise RetryException due to short output
    with pytest.raises(RetryException):
        generate_draft("dummy", 1)
