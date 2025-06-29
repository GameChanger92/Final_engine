from unittest.mock import patch, Mock
from src.context_builder import make_context, ContextBuilder


def test_make_context_with_korean_scenes():
    """Test with Korean scenes as specified in requirements."""
    scenes = ["씬1", "씬2", "씬3"]
    result = make_context(scenes)

    # Check that scenes are properly numbered
    assert "1. 씬1" in result
    assert "2. 씬2" in result
    assert "3. 씬3" in result
    
    # Check basic structure is present
    assert isinstance(result, str)
    assert len(result) > 0


def test_make_context_returns_string():
    """Test that the function returns a string."""
    scenes = ["scene1", "scene2"]
    result = make_context(scenes)
    assert isinstance(result, str)


@patch.object(ContextBuilder, 'load_knowledge_graph')
@patch.object(ContextBuilder, 'load_style_config')
@patch.object(ContextBuilder, 'get_similar_scenes')
def test_make_context_placeholders_present(mock_get_similar, mock_style, mock_kg):
    """Test that placeholder texts are present when no data is available."""
    # Mock to return empty data
    mock_kg.return_value = {}
    mock_style.return_value = {}
    mock_get_similar.return_value = []
    
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


@patch.object(ContextBuilder, 'load_knowledge_graph')
@patch.object(ContextBuilder, 'load_style_config')
@patch.object(ContextBuilder, 'get_similar_scenes')
def test_make_context_empty_list(mock_get_similar, mock_style, mock_kg):
    """Test behavior with empty scenes list."""
    # Mock to return empty data
    mock_kg.return_value = {}
    mock_style.return_value = {}
    mock_get_similar.return_value = []
    
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
    assert isinstance(result, str)


def test_make_context_multiline_format():
    """Test that the output is properly formatted as multiline string."""
    scenes = ["scene1", "scene2"]
    result = make_context(scenes)

    lines = result.split("\n")
    assert len(lines) >= 5  # Should have multiple sections
    
    # Check that scenes are numbered correctly
    scene_found = False
    for line in lines:
        if "1. scene1" in line:
            scene_found = True
            break
    assert scene_found, "Should contain numbered scene 1"
    
    scene_found = False  
    for line in lines:
        if "2. scene2" in line:
            scene_found = True
            break
    assert scene_found, "Should contain numbered scene 2"


def test_make_context_backward_compatibility():
    """Test that make_context works as a function (backward compatibility)."""
    scenes = ["test scene"]
    result = make_context(scenes)
    
    # Should return a string result
    assert isinstance(result, str)
    assert len(result) > 0
    
    # Should contain the scene
    assert "test scene" in result
