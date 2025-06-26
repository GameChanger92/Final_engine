from src.context_builder import make_context


def test_make_context_with_korean_scenes():
    """Test with Korean scenes as specified in requirements."""
    scenes = ["씬1", "씬2", "씬3"]
    result = make_context(scenes)

    # Check that all placeholder texts are present
    assert "[Character Info: TO BE ADDED]" in result
    assert "[Previous Episode: TO BE ADDED]" in result
    assert "[Vector Search: TO BE ADDED]" in result

    # Check that scenes are properly numbered
    assert "1. 씬1" in result
    assert "2. 씬2" in result
    assert "3. 씬3" in result


def test_make_context_returns_string():
    """Test that the function returns a string."""
    scenes = ["scene1", "scene2"]
    result = make_context(scenes)
    assert isinstance(result, str)


def test_make_context_placeholders_present():
    """Test that all required placeholder texts are present."""
    scenes = ["test scene"]
    result = make_context(scenes)

    assert "[Character Info: TO BE ADDED]" in result
    assert "[Previous Episode: TO BE ADDED]" in result
    assert "[Vector Search: TO BE ADDED]" in result


def test_make_context_scene_numbering():
    """Test that scenes are properly numbered starting from 1."""
    scenes = ["first scene", "second scene", "third scene"]
    result = make_context(scenes)

    assert "1. first scene" in result
    assert "2. second scene" in result
    assert "3. third scene" in result


def test_make_context_empty_list():
    """Test behavior with empty scenes list."""
    scenes = []
    result = make_context(scenes)

    # Should still contain placeholders even with empty scenes
    assert "[Character Info: TO BE ADDED]" in result
    assert "[Previous Episode: TO BE ADDED]" in result
    assert "[Vector Search: TO BE ADDED]" in result
    assert isinstance(result, str)


def test_make_context_single_scene():
    """Test with single scene."""
    scenes = ["only scene"]
    result = make_context(scenes)

    assert "1. only scene" in result
    assert "[Character Info: TO BE ADDED]" in result


def test_make_context_multiline_format():
    """Test that the output is properly formatted as multiline string."""
    scenes = ["scene1", "scene2"]
    result = make_context(scenes)

    lines = result.split("\n")
    assert len(lines) >= 5  # 3 placeholders + 1 empty line + 2 scenes
    assert lines[0] == "[Character Info: TO BE ADDED]"
    assert lines[1] == "[Previous Episode: TO BE ADDED]"
    assert lines[2] == "[Vector Search: TO BE ADDED]"
    assert lines[3] == ""  # Empty separator line
    assert lines[4] == "1. scene1"
    assert lines[5] == "2. scene2"
