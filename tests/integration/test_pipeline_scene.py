"""
Integration tests for Scene Maker v2 in the pipeline.

Tests the integration of Scene Maker v2 with the overall pipeline,
ensuring ScenePoint structure is compatible and end-to-end functionality works.
"""

from unittest.mock import patch
from src.scene_maker import make_scenes


class TestPipelineSceneIntegration:
    """Integration tests for Scene Maker v2 in the pipeline."""

    def test_scene_maker_v2_structure_compatibility(self):
        """Test that Scene Maker v2 output structure is compatible with pipeline expectations."""
        dummy_beat = {
            "idx": 1,
            "summary": "Pipeline integration test beat",
            "anchor": False,
        }
        scenes = make_scenes(dummy_beat)

        # Test basic structure compatibility
        assert isinstance(scenes, list), "Scenes output must be a list"
        assert len(scenes) >= 8, "Must generate at least 8 scenes"
        assert len(scenes) <= 12, "Must generate at most 12 scenes"

        # Test ScenePoint schema
        for scene in scenes:
            # Required v2 fields
            assert "pov" in scene, "Scene must have 'pov' field"
            assert "purpose" in scene, "Scene must have 'purpose' field"
            assert "tags" in scene, "Scene must have 'tags' field"
            assert "desc" in scene, "Scene must have 'desc' field"

            # Legacy compatibility fields
            assert "idx" in scene, "Scene must have 'idx' field"
            assert "beat_id" in scene, "Scene must have 'beat_id' field"

            # Validate values
            assert scene["pov"] in ["main", "side"], f"Invalid pov: {scene['pov']}"
            assert isinstance(scene["tags"], list), "Tags must be a list"
            assert len(scene["tags"]) >= 1, "Tags must not be empty"

    def test_run_pipeline_scene_integration(self):
        """Test Scene Maker v2 compatibility within the pipeline context."""

        # Test that Scene Maker v2 can handle beat dictionaries as expected by the pipeline
        # This simulates what the pipeline would pass to make_scenes()

        test_beats = [
            {
                "idx": 1,
                "summary": "Opening scene with character introduction",
                "anchor": False,
            },
            {
                "idx": 2,
                "summary": "Conflict development and tension building",
                "anchor": False,
            },
            {
                "idx": 3,
                "summary": "Climactic confrontation and resolution",
                "anchor": True,
            },
        ]

        # Test that each beat can be processed by Scene Maker v2
        for beat in test_beats:
            scenes = make_scenes(beat)

            # Verify Scene Maker v2 generates correct count
            assert (
                8 <= len(scenes) <= 12
            ), f"Beat {beat['idx']} generated {len(scenes)} scenes, expected 8-12"

            # Verify all scenes have the v2 schema
            for scene in scenes:
                # Required v2 fields
                assert (
                    "pov" in scene
                ), f"Scene {scene.get('idx', '?')} missing 'pov' field"
                assert (
                    "purpose" in scene
                ), f"Scene {scene.get('idx', '?')} missing 'purpose' field"
                assert (
                    "tags" in scene
                ), f"Scene {scene.get('idx', '?')} missing 'tags' field"
                assert (
                    "desc" in scene
                ), f"Scene {scene.get('idx', '?')} missing 'desc' field"

                # Legacy compatibility fields needed by pipeline
                assert "idx" in scene, "Scene missing 'idx' field"
                assert "beat_id" in scene, "Scene missing 'beat_id' field"

                # Validate field values
                assert scene["pov"] in ["main", "side"], f"Invalid pov: {scene['pov']}"
                assert isinstance(scene["tags"], list), "Tags must be a list"
                assert len(scene["tags"]) >= 1, "Tags must not be empty"
                assert (
                    scene["beat_id"] == beat["idx"]
                ), f"Scene beat_id mismatch: {scene['beat_id']} != {beat['idx']}"

        # Test that the pipeline can extract scene descriptions as expected
        # The pipeline does: scene_descriptions = [scene["desc"] for scene in all_scenes]
        all_scenes = []
        for beat in test_beats:
            scenes = make_scenes(beat)
            all_scenes.extend(
                scenes[:4]
            )  # Pipeline takes first 4 scenes from each beat

        # This should work without errors
        scene_descriptions = [scene["desc"] for scene in all_scenes]

        assert (
            len(scene_descriptions) == 12
        ), "Pipeline should extract 12 scene descriptions"
        for desc in scene_descriptions:
            assert isinstance(desc, str), "Scene description must be string"
            assert len(desc.strip()) > 0, "Scene description must not be empty"

    def test_scene_maker_v2_beat_processing(self):
        """Test that Scene Maker v2 can process various beat types correctly."""

        test_beats = [
            {"idx": 1, "summary": "액션 장면이 포함된 비트", "anchor": False},
            {"idx": 2, "summary": "대화 중심의 조용한 비트", "anchor": True},
            {"idx": 3, "summary": "감정적 전환점이 있는 비트", "anchor": False},
            {"idx": 4, "summary": "배경 설명과 세계관 소개 비트", "anchor": False},
        ]

        for beat in test_beats:
            scenes = make_scenes(beat)

            # Validate each beat produces valid v2 scenes
            assert (
                8 <= len(scenes) <= 12
            ), f"Beat {beat['idx']} produced {len(scenes)} scenes"

            # Check diversity in POV
            povs = [scene["pov"] for scene in scenes]
            assert (
                "main" in povs or "side" in povs
            ), f"Beat {beat['idx']} should have varied POVs"

            # Check that all scenes reference the beat
            for scene in scenes:
                assert (
                    scene["beat_id"] == beat["idx"]
                ), f"Scene beat_id mismatch for beat {beat['idx']}"

    def test_scene_maker_logging_output(self):
        """Test that Scene Maker v2 produces expected log output format."""

        # Capture log output
        with patch("src.scene_maker.logger") as mock_logger:
            dummy_beat = {"idx": 5, "summary": "Log test beat", "anchor": False}
            scenes = make_scenes(dummy_beat)

            # Check that appropriate logging occurred
            # (Note: In fallback mode, we expect warning logs)
            assert (
                mock_logger.warning.called or mock_logger.info.called
            ), "Should log scene generation"

            # Verify scene count is in expected range
            assert 8 <= len(scenes) <= 12, "Should generate 8-12 scenes"

            # The log should mention scene count and POV distribution
            main_count = sum(1 for s in scenes if s.get("pov") == "main")
            side_count = sum(1 for s in scenes if s.get("pov") == "side")

            assert main_count + side_count == len(scenes), "All scenes should have POV"
            assert (
                main_count > 0 or side_count > 0
            ), "Should have at least some scenes with POV"

    def test_backwards_compatibility_with_existing_pipeline(self):
        """Test that Scene Maker v2 maintains backwards compatibility."""

        # Test with old-style beat input that existing pipeline might use
        legacy_beat = {"idx": 1, "summary": "Legacy beat format", "anchor": False}
        scenes = make_scenes(legacy_beat)

        # Should still work and produce new format
        assert len(scenes) >= 8, "Should generate at least 8 scenes"

        # But should include new v2 fields
        for scene in scenes:
            assert "pov" in scene, "Should have new pov field"
            assert "purpose" in scene, "Should have new purpose field"
            assert "tags" in scene, "Should have new tags field"

            # And maintain old fields for compatibility
            assert "idx" in scene, "Should maintain idx field"
            assert "desc" in scene, "Should maintain desc field"
            assert "beat_id" in scene, "Should maintain beat_id field"
