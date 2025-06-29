"""
Tests for the enhanced context builder in src/context_builder.py
"""

import pytest
from unittest.mock import Mock, patch

from src.context_builder import ContextBuilder, make_context


class TestContextBuilder:
    """Test cases for the enhanced ContextBuilder class."""

    @pytest.fixture
    def context_builder(self, project_id):
        """Create a ContextBuilder instance for testing."""
        return ContextBuilder(project=project_id)

    @pytest.fixture
    def sample_scenes(self):
        """Sample scenes for testing."""
        return ["첫 번째 씬입니다", "두 번째 씬입니다", "세 번째 씬입니다"]

    @pytest.fixture
    def sample_kg_data(self):
        """Sample knowledge graph data."""
        return {
            "characters": {
                "MC": {
                    "name": "테스트 주인공",
                    "background": "학생",
                    "traits": ["brave", "smart"],
                    "relationships": ["Alice"],
                }
            },
            "story_elements": {
                "themes": ["성장", "모험"],
                "tone": "청춘",
                "genre": "판타지",
            },
        }

    @pytest.fixture
    def sample_style_config(self):
        """Sample style configuration."""
        return {
            "platform": "문피아",
            "style": {
                "tone": "친근한",
                "voice": "1인칭",
                "description_level": "detailed",
            },
            "word_count_target": 2000,
        }

    def test_context_builder_initialization(self, project_id):
        """Test ContextBuilder initialization."""
        builder = ContextBuilder(project=project_id)
        assert builder.project == project_id
        assert builder.vector_store is not None
        assert builder.jinja_env is not None

    def test_load_knowledge_graph_exists(self, context_builder, tmp_path):
        """Test loading knowledge graph when file exists."""
        # The file should already exist from conftest.py setup
        kg_data = context_builder.load_knowledge_graph()
        assert isinstance(kg_data, dict)

    def test_load_knowledge_graph_missing(self, tmp_path):
        """Test loading knowledge graph when file is missing."""
        builder = ContextBuilder(project="nonexistent_project")
        kg_data = builder.load_knowledge_graph()
        assert kg_data == {}

    def test_load_style_config_exists(self, context_builder):
        """Test loading style config when file exists."""
        style_data = context_builder.load_style_config()
        assert isinstance(style_data, dict)
        assert "platform" in style_data

    def test_load_style_config_missing(self, tmp_path):
        """Test loading style config when file is missing."""
        builder = ContextBuilder(project="nonexistent_project")
        style_data = builder.load_style_config()
        assert style_data["platform"] == "default"
        assert style_data["word_count_target"] == 2000

    def test_get_similar_scenes_with_text(self, context_builder):
        """Test getting similar scenes with valid text."""
        similar_scenes = context_builder.get_similar_scenes("테스트 씬")
        assert isinstance(similar_scenes, list)
        # Should be empty initially as vector store is likely empty
        assert len(similar_scenes) >= 0

    def test_get_similar_scenes_empty_text(self, context_builder):
        """Test getting similar scenes with empty text."""
        similar_scenes = context_builder.get_similar_scenes("")
        assert similar_scenes == []

    def test_get_similar_scenes_none_text(self, context_builder):
        """Test getting similar scenes with None text."""
        similar_scenes = context_builder.get_similar_scenes(None)
        assert similar_scenes == []

    @patch("src.context_builder.VectorStore")
    def test_get_similar_scenes_with_results(self, mock_vector_store, context_builder):
        """Test getting similar scenes with mocked results."""
        # Mock vector store to return sample results
        mock_instance = Mock()
        mock_instance.similar.return_value = [
            ("scene_1", 0.95),
            ("scene_2", 0.87),
            ("scene_3", 0.75),
        ]
        mock_vector_store.return_value = mock_instance

        # Create new builder with mocked vector store
        builder = ContextBuilder(project="test")
        builder.vector_store = mock_instance

        similar_scenes = builder.get_similar_scenes("테스트 씬", top_k=3)
        assert len(similar_scenes) == 3
        assert similar_scenes[0] == ("scene_1", 0.95)

    def test_build_context_basic(self, context_builder, sample_scenes):
        """Test basic context building."""
        context = context_builder.build_context(sample_scenes)
        assert isinstance(context, str)
        assert len(context) > 0

        # Should contain scene numbering
        assert "1. 첫 번째 씬입니다" in context
        assert "2. 두 번째 씬입니다" in context
        assert "3. 세 번째 씬입니다" in context

    def test_build_context_with_previous_episode(self, context_builder, sample_scenes):
        """Test context building with previous episode."""
        previous_ep = "이전 에피소드 요약입니다."
        context = context_builder.build_context(
            sample_scenes, previous_episode=previous_ep
        )
        assert previous_ep in context

    def test_build_context_with_vector_text(self, context_builder, sample_scenes):
        """Test context building with specific vector search text."""
        vector_text = "특별한 벡터 검색용 텍스트"
        context = context_builder.build_context(
            sample_scenes, scene_text_for_vector=vector_text
        )
        assert isinstance(context, str)
        assert len(context) > 0

    def test_build_context_empty_scenes(self, context_builder):
        """Test context building with empty scenes list."""
        context = context_builder.build_context([])
        assert isinstance(context, str)
        # Should still have basic structure even with no scenes

    @patch("src.context_builder.VectorStore")
    def test_build_context_with_similar_scenes(
        self, mock_vector_store, context_builder, sample_scenes
    ):
        """Test context building includes similar scenes."""
        # Mock vector store to return sample results
        mock_instance = Mock()
        mock_instance.similar.return_value = [
            ("similar_scene_1", 0.89),
            ("similar_scene_2", 0.76),
        ]
        mock_vector_store.return_value = mock_instance

        builder = ContextBuilder(project="test")
        builder.vector_store = mock_instance

        with patch.object(builder, "load_knowledge_graph", return_value={}):
            with patch.object(
                builder, "load_style_config", return_value={"platform": "test"}
            ):
                context = builder.build_context(sample_scenes)

        assert "similar_scene_1" in context
        assert "0.89" in context

    def test_fallback_context(self, context_builder, sample_scenes):
        """Test fallback context generation."""
        similar_scenes = [("scene_1", 0.85), ("scene_2", 0.70)]
        context = context_builder._fallback_context(sample_scenes, similar_scenes)

        assert "[Character Info: TO BE ADDED]" in context
        assert "[Previous Episode: TO BE ADDED]" in context
        assert "Vector Search Results:" in context
        assert "scene_1 (similarity: 0.85)" in context
        assert "1. 첫 번째 씬입니다" in context

    def test_template_rendering_error_handling(self, context_builder, sample_scenes):
        """Test that template errors are handled gracefully."""
        # Force template not found error by using non-existent template directory
        context_builder.jinja_env.loader.searchpath = ["/nonexistent/path"]

        context = context_builder.build_context(sample_scenes)

        # Should fallback to simple format
        assert isinstance(context, str)
        assert "[Character Info: TO BE ADDED]" in context

    def test_make_context_backward_compatibility(self, sample_scenes):
        """Test backward compatibility function."""
        context = make_context(sample_scenes)
        assert isinstance(context, str)
        assert "1. 첫 번째 씬입니다" in context
        assert "2. 두 번째 씬입니다" in context

    def test_korean_content_handling(self, context_builder):
        """Test handling of Korean content specifically."""
        korean_scenes = ["한글 씬 1", "한글 씬 2", "한글 씬 3"]
        context = context_builder.build_context(korean_scenes)

        assert "한글 씬 1" in context
        assert "한글 씬 2" in context
        assert "한글 씬 3" in context

    @patch("src.context_builder.logger")
    def test_logging_similar_scenes(self, mock_logger, context_builder, sample_scenes):
        """Test that similar scenes are logged properly."""
        with patch.object(context_builder, "get_similar_scenes") as mock_get_similar:
            mock_get_similar.return_value = [("scene_1", 0.9), ("scene_2", 0.8)]

            context_builder.build_context(sample_scenes)

            # Should log the number of similar scenes found
            mock_logger.info.assert_called_with("Context built with 2 similar scenes")

    def test_vector_search_error_handling(self, context_builder, sample_scenes):
        """Test error handling in vector search."""
        with patch.object(
            context_builder.vector_store,
            "similar",
            side_effect=Exception("Vector error"),
        ):
            similar_scenes = context_builder.get_similar_scenes("test")
            assert similar_scenes == []

    def test_json_loading_error_handling(self, context_builder):
        """Test error handling for corrupted JSON files."""
        with patch("builtins.open", side_effect=OSError("File error")):
            kg_data = context_builder.load_knowledge_graph()
            style_data = context_builder.load_style_config()

            assert kg_data == {}
            assert style_data["platform"] == "default"


class TestIntegration:
    """Integration tests for the context builder."""

    def test_full_integration_with_data_files(self, project_id):
        """Test full integration with actual data files."""
        builder = ContextBuilder(project=project_id)
        scenes = ["통합 테스트 씬 1", "통합 테스트 씬 2"]

        context = builder.build_context(scenes)

        assert isinstance(context, str)
        assert len(context) > 0
        assert "통합 테스트 씬 1" in context
        assert "통합 테스트 씬 2" in context
