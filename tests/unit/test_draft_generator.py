from src.draft_generator import generate_draft


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


def test_generate_draft_contains_placeholder_content():
    """Test that the draft contains expected placeholder content."""
    context = "Test context"
    episode_num = 1
    result = generate_draft(context, episode_num)

    assert "[PLACEHOLDER DRAFT CONTENT]" in result
    assert "stub implementation" in result.lower()


def test_generate_draft_mentions_context_length():
    """Test that the draft mentions the context length."""
    context = "This is a test context with specific length"
    episode_num = 1
    result = generate_draft(context, episode_num)

    expected_length = len(context)
    assert f"{expected_length} characters" in result


def test_generate_draft_multiline_format():
    """Test that the output is properly formatted as multiline string."""
    context = "Test context"
    episode_num = 1
    result = generate_draft(context, episode_num)

    lines = result.split("\n")
    assert len(lines) > 5  # Should have multiple lines
    assert lines[0].startswith("=== Episode")
    assert lines[0].endswith("Draft ===")


def test_generate_draft_different_contexts_different_lengths():
    """Test that different context lengths are correctly reported."""
    short_context = "short"
    long_context = "This is a much longer context string for testing purposes"
    episode_num = 1

    short_result = generate_draft(short_context, episode_num)
    long_result = generate_draft(long_context, episode_num)

    assert f"{len(short_context)} characters" in short_result
    assert f"{len(long_context)} characters" in long_result
    assert short_result != long_result  # Results should be different


def test_generate_draft_zero_episode_number():
    """Test behavior with edge case episode number."""
    context = "Test context"
    episode_num = 0
    result = generate_draft(context, episode_num)

    assert isinstance(result, str)
    assert "Episode 0" in result


def test_generate_draft_empty_context():
    """Test behavior with empty context."""
    context = ""
    episode_num = 1
    result = generate_draft(context, episode_num)

    assert isinstance(result, str)
    assert "Episode 1" in result
    assert "0 characters" in result  # Empty context has 0 characters
