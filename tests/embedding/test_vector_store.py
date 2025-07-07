"""
test_vector_store.py

Comprehensive tests for VectorStore embedding functionality.
Tests embedding storage, similarity search, and edge cases.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.embedding.embedder import embed_scene
from src.embedding.vector_store import VectorStore


@pytest.fixture
def set_unit_test_mode(monkeypatch):
    """Set UNIT_TEST_MODE and disable FAST_MODE for all tests in this module."""
    monkeypatch.setenv("UNIT_TEST_MODE", "1")
    monkeypatch.setenv("FAST_MODE", "0")


@pytest.mark.usefixtures("set_unit_test_mode")
class TestVectorStore:
    """Test VectorStore functionality."""

    @pytest.fixture
    def temp_project(self):
        """Create a temporary project for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create project structure
            project_dir = temp_path / "projects" / "test_project"
            data_dir = project_dir / "data"
            data_dir.mkdir(parents=True, exist_ok=True)

            # Create embedding config
            config = {
                "model": "text-embedding-3-small",
                "chroma_path": str(project_dir / "db"),
            }
            config_path = data_dir / "embedding_config.json"
            with open(config_path, "w") as f:
                json.dump(config, f)

            # Patch the data_path function to use our temp directory
            with patch("src.embedding.vector_store.data_path") as mock_data_path:
                mock_data_path.return_value = config_path

                # Also patch the Path construction in _get_db_path
                with patch.object(VectorStore, "_get_db_path") as mock_get_db_path:
                    mock_get_db_path.return_value = project_dir / "db"
                    yield "test_project"

    def test_vector_store_initialization(self, temp_project):
        """Test VectorStore initializes correctly."""
        with VectorStore(temp_project, test_mode=True) as store:
            assert store.project == temp_project
            assert store.config["model"] == "text-embedding-3-small"
            assert store.collection is not None

    def test_add_and_count(self, temp_project):
        """Test adding scenes and counting them."""
        with VectorStore(temp_project, test_mode=True) as store:
            # Initially should be empty
            assert store.count() == 0

            # Add a scene
            success = store.add("scene_001", "Hero defeats the dragon")
            assert success is True
            assert store.count() == 1

            # Add another scene
            success = store.add("scene_002", "Princess escapes from castle")
            assert success is True
            assert store.count() == 2

    def test_similar_search_basic(self, temp_project):
        """Test basic similarity search functionality."""
        with VectorStore(temp_project, test_mode=True) as store:
            # Add some scenes
            store.add("scene_001", "Hero fights dragon with sword")
            store.add("scene_002", "Princess sings in garden")
            store.add("scene_003", "Dragon breathes fire at village")

            # Search for dragon-related content
            results = store.similar("dragon battle", top_k=2)

            assert len(results) <= 2
            assert all(isinstance(result, tuple) for result in results)
            assert all(len(result) == 2 for result in results)
            assert all(isinstance(result[0], str) for result in results)  # scene_id
            assert all(isinstance(result[1], float) for result in results)  # score

    def test_similarity_scores_ordering(self, temp_project):
        """Test that similarity scores are in descending order."""
        with VectorStore(temp_project, test_mode=True) as store:
            # Add scenes with varying relevance to "dragon"
            store.add("scene_001", "Dragon flies majestically over the mountain peaks")
            store.add("scene_002", "Knight polishes his armor in silence")
            store.add("scene_003", "The fearsome dragon breathes fire")

            results = store.similar("dragon", top_k=3)

            # Scores should be in descending order (most similar first)
            assert results[0][1] >= results[1][1] >= results[2][1]

    def test_clear_functionality(self, temp_project):
        """Test clearing the vector store."""
        with VectorStore(temp_project, test_mode=True) as store:
            # Add some scenes
            store.add("scene_001", "Content 1")
            store.add("scene_002", "Content 2")
            assert store.count() == 2

            # Clear the store
            success = store.clear()
            assert success is True
            assert store.count() == 0

            # Should be able to add after clearing
            store.add("scene_003", "New content")
            assert store.count() == 1

    def test_duplicate_scene_id_handling(self, temp_project):
        """Test handling of duplicate scene IDs."""
        with VectorStore(temp_project, test_mode=True) as store:
            # Add a scene
            store.add("scene_001", "Original content")
            assert store.count() == 1

            # Add same scene ID with different content
            # ChromaDB should handle this by updating or adding
            store.add("scene_001", "Updated content")

            # Count might stay the same (update) or increase (duplicate handling)
            # The exact behavior depends on ChromaDB implementation
            assert store.count() >= 1

    def test_config_file_missing(self, temp_project):
        """Test behavior when config file is missing."""
        # Don't create a config file
        with patch("src.embedding.vector_store.data_path") as mock_data_path:
            non_existent_path = Path("/tmp/non_existent_config.json")
            mock_data_path.return_value = non_existent_path

            with patch.object(VectorStore, "_get_db_path") as mock_get_db_path:
                mock_get_db_path.return_value = Path("/tmp/test_db")

                with VectorStore(temp_project) as store:
                    # Should use default config
                    assert store.config["model"] == "text-embedding-3-small"
                    assert "chroma_path" in store.config

    def test_config_file_malformed(self, temp_project):
        """Test behavior with malformed config file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("invalid json content")
            malformed_config_path = Path(f.name)

        try:
            with patch("src.embedding.vector_store.data_path") as mock_data_path:
                mock_data_path.return_value = malformed_config_path

                with patch.object(VectorStore, "_get_db_path") as mock_get_db_path:
                    mock_get_db_path.return_value = Path("/tmp/test_db")

                    with VectorStore(temp_project) as store:
                        # Should fallback to default config
                        assert store.config["model"] == "text-embedding-3-small"
        finally:
            malformed_config_path.unlink()

    def test_add_empty_text_handling(self, temp_project):
        """Test handling of empty text in add method."""
        with VectorStore(temp_project, test_mode=True) as store:
            # Adding empty text should fail gracefully
            success = store.add("scene_001", "")
            assert success is False
            assert store.count() == 0

            # Adding whitespace-only text should also fail
            success = store.add("scene_002", "   ")
            assert success is False
            assert store.count() == 0

    def test_embedding_generation_failure(self, temp_project):
        """Test handling of embedding generation failures."""
        with VectorStore(temp_project, test_mode=True) as store:
            # Mock embed_scene to raise an exception
            with patch("src.embedding.vector_store.embed_scene") as mock_embed:
                mock_embed.side_effect = RuntimeError("API failure")

                success = store.add("scene_001", "Some content")
                assert success is False
                assert store.count() == 0

    def test_search_with_api_failure(self, temp_project):
        """Test similarity search when embedding generation fails."""
        with VectorStore(temp_project, test_mode=True) as store:
            # Add a scene first (this should work)
            store.add("scene_001", "Some content")

            # Mock embed_scene to fail for query (patch at module level)
            with patch("src.embedding.vector_store.embed_scene") as mock_embed:
                mock_embed.side_effect = RuntimeError("API failure")

                results = store.similar("query text", top_k=5)
                assert results == []


class TestEmbedder:
    """Test embedder functionality."""

    @patch.dict("os.environ", {"UNIT_TEST_MODE": "1", "FAST_MODE": "0"})
    def test_embed_scene_empty_text(self):
        """Test embedding empty text raises ValueError."""
        with pytest.raises(ValueError, match="Text cannot be empty"):
            embed_scene("")

        with pytest.raises(ValueError, match="Text cannot be empty"):
            embed_scene("   ")

    @patch.dict("os.environ", {"UNIT_TEST_MODE": "1", "FAST_MODE": "0"})
    def test_embed_scene_no_api_key(self):
        """Test embedding without API key returns dummy embedding."""
        with patch.dict("os.environ", {}, clear=True):
            # Remove OPENAI_API_KEY if it exists
            if "OPENAI_API_KEY" in os.environ:
                del os.environ["OPENAI_API_KEY"]

            result = embed_scene("test text")
            assert isinstance(result, list)
            assert len(result) == 1536
            assert all(isinstance(x, float) for x in result)

    @patch("openai.OpenAI")
    @patch.dict("os.environ", {"UNIT_TEST_MODE": "1", "FAST_MODE": "0"})
    def test_embed_scene_api_success(self, mock_openai):
        """Test successful embedding generation."""
        # Mock OpenAI response
        mock_response = MagicMock()
        mock_response.data = [MagicMock()]
        mock_response.data[0].embedding = [0.1, 0.2, 0.3]

        mock_client = MagicMock()
        mock_client.embeddings.create.return_value = mock_response
        mock_openai.return_value = mock_client

        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
            result = embed_scene("test text")
            assert result == [0.1, 0.2, 0.3]

    @patch("openai.OpenAI")
    @patch.dict("os.environ", {"UNIT_TEST_MODE": "1", "FAST_MODE": "0"})
    def test_embed_scene_api_failure(self, mock_openai):
        """Test embedding generation failure."""
        mock_client = MagicMock()
        mock_client.embeddings.create.side_effect = Exception("API Error")
        mock_openai.return_value = mock_client

        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
            with pytest.raises(RuntimeError, match="Failed to generate embedding"):
                embed_scene("test text")
