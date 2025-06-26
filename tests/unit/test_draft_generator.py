from src.draft_generator import generate_draft


def test_generate_draft_placeholder_text():
    """Test that the output contains 'PLACEHOLDER' text."""
    context = "Test context"
    result = generate_draft(context)
    assert "PLACEHOLDER" in result


def test_generate_draft_episode_num_in_output():
    """Test that episode_num is included in the output."""
    context = "Test context"
    episode_num = 5
    result = generate_draft(context, episode_num)
    assert f"EPISODE {episode_num}" in result


def test_generate_draft_default_episode_num():
    """Test that default episode number is 1."""
    context = "Test context"
    result = generate_draft(context)
    assert "EPISODE 1" in result


def test_generate_draft_context_truncation():
    """Test that context is truncated to 200 characters."""
    # Create a context longer than 200 characters
    long_context = "a" * 250
    result = generate_draft(long_context)

    # Should contain exactly 200 'a's plus ellipsis
    expected_content = "a" * 200 + "..."
    assert expected_content in result


def test_generate_draft_short_context_no_truncation():
    """Test that short context is not truncated."""
    short_context = "Short context"
    result = generate_draft(short_context)

    # Should contain the full context without ellipsis
    assert short_context in result
    assert not result.endswith("...")


def test_generate_draft_exact_200_chars():
    """Test context that is exactly 200 characters."""
    context_200 = "a" * 200
    result = generate_draft(context_200)

    # Should contain all 200 characters without ellipsis
    assert context_200 in result
    assert not result.endswith("...")


def test_generate_draft_format_structure():
    """Test that the output has the correct format structure."""
    context = "Test context"
    episode_num = 3
    result = generate_draft(context, episode_num)

    lines = result.split("\n")
    assert lines[0] == f"PLACEHOLDER EPISODE {episode_num}"
    assert lines[1] == ""  # Empty line
    assert lines[2] == context


def test_generate_draft_korean_context():
    """Test with Korean text context."""
    korean_context = "한글 컨텍스트 테스트"
    result = generate_draft(korean_context)

    assert "PLACEHOLDER" in result
    assert "EPISODE 1" in result
    assert korean_context in result


def test_generate_draft_empty_context():
    """Test with empty context."""
    empty_context = ""
    result = generate_draft(empty_context)

    assert "PLACEHOLDER EPISODE 1" in result
    assert result.endswith("\n\n")  # Should end with double newline and empty context


def test_generate_draft_multiline_context():
    """Test with multiline context."""
    multiline_context = "Line 1\nLine 2\nLine 3"
    result = generate_draft(multiline_context)

    assert "PLACEHOLDER" in result
    assert multiline_context in result
