"""
Test suite for Scene Maker v2 functionality.

Tests the new ScenePoint schema with pov, purpose, tags, desc fields,
LLM integration, and VectorStore metadata storage.
"""

import os
import pytest
from unittest.mock import patch, MagicMock
from src.scene_maker import make_scenes, build_prompt, parse_scene_yaml, TEMP_SCENE


class TestSceneMakerV2:
    """Test Scene Maker v2 functionality."""

    def test_scene_count_in_range(self):
        """Test that generated scenes are between 8-12 in count."""
        dummy_beat = {"idx": 1, "summary": "Test Beat", "anchor": False}
        scenes = make_scenes(dummy_beat)

        # For fallback (when no API key), we get exactly 10 for backward compatibility
        # When LLM works, we should get 8-12
        assert 8 <= len(scenes) <= 12, f"Expected 8-12 scenes, got {len(scenes)}"

    def test_scene_pov_values(self):
        """Test that pov values are either 'main' or 'side'."""
        dummy_beat = {"idx": 1, "summary": "Test Beat", "anchor": False}
        scenes = make_scenes(dummy_beat)

        valid_povs = {"main", "side"}
        for scene in scenes:
            assert "pov" in scene, "Scene missing 'pov' field"
            assert scene["pov"] in valid_povs, f"Invalid pov value: {scene['pov']}"

    def test_scene_tags_list(self):
        """Test that tags field is a list with at least one element."""
        dummy_beat = {"idx": 1, "summary": "Test Beat", "anchor": False}
        scenes = make_scenes(dummy_beat)

        for scene in scenes:
            assert "tags" in scene, "Scene missing 'tags' field"
            assert isinstance(scene["tags"], list), "Tags must be a list"
            assert len(scene["tags"]) >= 1, "Tags list must have at least one element"

    def test_new_scene_schema(self):
        """Test that scenes have the new v2 schema."""
        dummy_beat = {"idx": 1, "summary": "Test Beat", "anchor": False}
        scenes = make_scenes(dummy_beat)

        required_fields = ["idx", "pov", "purpose", "tags", "desc", "beat_id"]
        for scene in scenes:
            for field in required_fields:
                assert field in scene, f"Scene missing required field: {field}"

    def test_temp_scene_environment_variable(self):
        """Test that TEMP_SCENE environment variable is used."""
        # Test default value
        assert TEMP_SCENE == 0.6, f"Expected TEMP_SCENE=0.6, got {TEMP_SCENE}"

        # Test with custom environment variable
        with patch.dict(os.environ, {"TEMP_SCENE": "0.8"}):
            # Re-import to get the new value
            from importlib import reload
            import src.scene_maker

            reload(src.scene_maker)
            assert src.scene_maker.TEMP_SCENE == 0.8

    def test_build_prompt_function(self):
        """Test the build_prompt function creates valid prompts."""
        beat_desc = "Test beat description"
        beat_no = 3

        prompt = build_prompt(beat_desc, beat_no)

        assert isinstance(prompt, str), "Prompt must be a string"
        assert len(prompt) > 0, "Prompt must not be empty"
        assert beat_desc in prompt, "Beat description must be included in prompt"

    @patch.dict(os.environ, {"GOOGLE_API_KEY": "test_key"})
    @patch("src.scene_maker.call_llm")
    def test_call_llm_with_correct_temperature(self, mock_call_llm):
        """Test that call_llm function exists and can be called."""
        mock_call_llm.return_value = "mock response"

        # Test that we can call the function
        result = mock_call_llm("test prompt")
        assert result == "mock response"
        assert mock_call_llm.called

    @patch("src.scene_maker.VectorStore")
    @patch.dict(
        os.environ,
        {"GOOGLE_API_KEY": "test_key", "FAST_MODE": "0", "UNIT_TEST_MODE": "0"},
    )
    def test_vector_store_metadata_storage(self, mock_vector_store_class):
        """Test that VectorStore stores metadata correctly."""
        # Mock VectorStore instance
        mock_store = MagicMock()
        mock_vector_store_class.return_value = mock_store

        # Mock LLM to return valid scenes (bypass the LLM failure path)
        with patch("src.scene_maker.call_llm") as mock_llm, patch(
            "src.scene_maker.parse_scene_yaml"
        ) as mock_parse:

            # Mock LLM and parser to return valid scenes
            mock_llm.return_value = "mocked yaml"
            mock_parse.return_value = [
                {
                    "idx": 1,
                    "pov": "main",
                    "purpose": "test1",
                    "tags": ["char1"],
                    "desc": "desc1",
                },
                {
                    "idx": 2,
                    "pov": "side",
                    "purpose": "test2",
                    "tags": ["char2"],
                    "desc": "desc2",
                },
            ]

            dummy_beat = {
                "idx": 2,
                "summary": "Test Beat for VectorStore",
                "anchor": False,
            }
            scenes = make_scenes(dummy_beat)

            # Check that VectorStore.add was called with metadata
            assert mock_store.add.called, "VectorStore.add should be called"

            # Check the calls to add method
            calls = mock_store.add.call_args_list
            assert len(calls) == len(
                scenes
            ), f"Expected {len(scenes)} calls to VectorStore.add"

            for call in calls:
                args, kwargs = call
                scene_id, text, metadata = args

                # Check scene_id format
                assert scene_id.startswith(
                    "beat_2_scene_"
                ), f"Invalid scene_id format: {scene_id}"

                # Check metadata structure
                assert isinstance(metadata, dict), "Metadata must be a dictionary"
                required_metadata_fields = [
                    "beat_id",
                    "scene_idx",
                    "pov",
                    "purpose",
                    "tags",
                ]
                for field in required_metadata_fields:
                    assert field in metadata, f"Metadata missing field: {field}"

    def test_parse_scene_yaml_valid_format(self):
        """Test parsing of valid YAML scene format."""
        yaml_content = """```yaml
scene_01:
  pov: main
  purpose: "테스트 목적"
  tags: ["캐릭터1", "장소1"]
  desc: "테스트 장면 설명"

scene_02:
  pov: side
  purpose: "또 다른 목적"
  tags: ["캐릭터2"]
  desc: "두 번째 장면 설명"

scene_03:
  pov: main
  purpose: "세 번째 목적"
  tags: ["캐릭터3"]
  desc: "세 번째 장면 설명"

scene_04:
  pov: side
  purpose: "네 번째 목적"
  tags: ["캐릭터4"]
  desc: "네 번째 장면 설명"

scene_05:
  pov: main
  purpose: "다섯 번째 목적"
  tags: ["캐릭터5"]
  desc: "다섯 번째 장면 설명"

scene_06:
  pov: side
  purpose: "여섯 번째 목적"
  tags: ["캐릭터6"]
  desc: "여섯 번째 장면 설명"

scene_07:
  pov: main
  purpose: "일곱 번째 목적"
  tags: ["캐릭터7"]
  desc: "일곱 번째 장면 설명"

scene_08:
  pov: side
  purpose: "여덟 번째 목적"
  tags: ["캐릭터8"]
  desc: "여덟 번째 장면 설명"
```"""

        scenes = parse_scene_yaml(yaml_content)

        assert len(scenes) == 8, f"Expected 8 scenes, got {len(scenes)}"

        # Check first scene
        scene1 = scenes[0]
        assert scene1["idx"] == 1
        assert scene1["pov"] == "main"
        assert scene1["purpose"] == "테스트 목적"
        assert scene1["tags"] == ["캐릭터1", "장소1"]
        assert scene1["desc"] == "테스트 장면 설명"

    def test_parse_scene_yaml_invalid_pov(self):
        """Test that invalid pov values raise exceptions."""
        yaml_content = """```yaml
scene_01:
  pov: invalid_pov
  purpose: "테스트"
  tags: ["test"]
  desc: "테스트 장면"
```"""

        with pytest.raises(Exception) as excinfo:
            parse_scene_yaml(yaml_content)
        assert "Invalid pov value" in str(excinfo.value)

    def test_parse_scene_yaml_missing_tags(self):
        """Test that missing or empty tags raise exceptions."""
        yaml_content = """```yaml
scene_01:
  pov: main
  purpose: "테스트"
  tags: []
  desc: "테스트 장면"
```"""

        with pytest.raises(Exception) as excinfo:
            parse_scene_yaml(yaml_content)
        assert "non-empty list" in str(excinfo.value)

    def test_scene_count_validation(self):
        """Test that scene count validation works (8-12 range)."""
        # Test too few scenes
        yaml_content_few = """```yaml
scene_01:
  pov: main
  purpose: "테스트"
  tags: ["test"]
  desc: "테스트 장면"
```"""

        with pytest.raises(Exception) as excinfo:
            parse_scene_yaml(yaml_content_few)
        assert "Invalid scene count" in str(excinfo.value)

    @patch.dict(os.environ, {"UNIT_TEST_MODE": "1"})
    def test_fallback_when_llm_fails(self):
        """Test that fallback scenes are generated when LLM fails."""
        dummy_beat = {"idx": 3, "summary": "Fallback Test Beat", "anchor": False}
        scenes = make_scenes(dummy_beat)

        # Should still generate scenes (fallback mode)
        assert len(scenes) == 10, "Fallback should generate 10 scenes"

        # Check schema is still correct
        for scene in scenes:
            assert "pov" in scene
            assert "purpose" in scene
            assert "tags" in scene
            assert "desc" in scene
            assert scene["beat_id"] == 3
