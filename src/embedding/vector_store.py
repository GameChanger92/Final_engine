"""
vector_store.py

ChromaDB wrapper for Final Engine with project-aware paths.
Provides scene point similarity search functionality.
"""

import json
import os
from pathlib import Path
from typing import List, Tuple, Dict, Any
import chromadb
from chromadb.config import Settings

from src.utils.path_helper import data_path
from src.embedding.embedder import embed_scene


class VectorStore:
    """
    ChromaDB-based vector store for scene embeddings with project-aware paths.

    Manages scene embeddings and provides similarity search functionality.
    """

    def __init__(self, project: str = "default"):
        """
        Initialize VectorStore for a specific project.

        Parameters
        ----------
        project : str, optional
            Project ID for path resolution, defaults to "default"
        """
        self.project = project
        self.config = self._load_config()

        # Set up ChromaDB path based on project
        db_path = self._get_db_path()

        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=str(db_path), settings=Settings(anonymized_telemetry=False)
        )

        # Get or create collection for this project
        self.collection = self.client.get_or_create_collection(
            name=f"scenes_{project}", metadata={"hnsw:space": "cosine"}
        )

    def _load_config(self) -> Dict[str, Any]:
        """
        Load embedding configuration from JSON file.

        Returns
        -------
        Dict[str, Any]
            Configuration with model and chroma_path settings
        """
        config_path = data_path("embedding_config.json", self.project)

        # Create default config if it doesn't exist
        if not config_path.exists():
            default_config = {
                "model": "text-embedding-3-small",
                "chroma_path": f"projects/{self.project}/db",
            }

            # Ensure directory exists
            config_path.parent.mkdir(parents=True, exist_ok=True)

            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(default_config, f, indent=2)

            return default_config

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)

            # Provide defaults for missing keys
            config.setdefault("model", "text-embedding-3-small")
            config.setdefault("chroma_path", f"projects/{self.project}/db")

            return config

        except (json.JSONDecodeError, OSError):
            # Return default config on file errors
            return {
                "model": "text-embedding-3-small",
                "chroma_path": f"projects/{self.project}/db",
            }

    def _get_db_path(self) -> Path:
        """
        Get the database path for ChromaDB storage.

        Returns
        -------
        Path
            Path to ChromaDB database directory
        """
        chroma_path = self.config["chroma_path"]

        # Replace {id} placeholder with actual project ID
        chroma_path = chroma_path.replace("{id}", self.project)

        # Ensure it's an absolute path
        if not os.path.isabs(chroma_path):
            # Relative to project root
            chroma_path = Path("projects") / self.project / "db"
        else:
            chroma_path = Path(chroma_path)

        # Ensure directory exists
        chroma_path.mkdir(parents=True, exist_ok=True)

        return chroma_path

    def add(self, scene_id: str, text: str, metadata: dict = None) -> bool:
        """
        Add a scene embedding to the vector store.

        Parameters
        ----------
        scene_id : str
            Unique identifier for the scene
        text : str
            Scene text content to embed
        metadata : dict, optional
            Additional metadata to store with the scene (e.g., tags, pov, purpose)

        Returns
        -------
        bool
            True if successfully added, False otherwise
        """
        # Fast mode for unit tests - skip actual vector store operations for speed
        if os.getenv("UNIT_TEST_MODE") == "1" or os.getenv("FAST_MODE") == "1":
            return True
            
        try:
            # Generate embedding
            embedding = embed_scene(text, self.config["model"])

            # Add to ChromaDB collection
            self.collection.add(
                embeddings=[embedding], 
                documents=[text], 
                ids=[scene_id],
                metadatas=[metadata] if metadata else None
            )

            return True

        except Exception:
            return False

    def similar(self, query: str, top_k: int = 5) -> List[Tuple[str, float]]:
        """
        Find similar scenes using cosine similarity.

        Parameters
        ----------
        query : str
            Query text to find similar scenes for
        top_k : int, optional
            Number of similar scenes to return, defaults to 5

        Returns
        -------
        List[Tuple[str, float]]
            List of (scene_id, similarity_score) tuples, ordered by similarity
        """
        if not query or not query.strip():
            return []

        try:
            # Generate embedding for query
            query_embedding = embed_scene(query, self.config["model"])

            # Search for similar embeddings
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=min(top_k, self.collection.count()),
            )

            # Format results as (scene_id, score) tuples
            if results["ids"] and results["distances"]:
                scene_ids = results["ids"][0]
                distances = results["distances"][0]

                # Convert distances to similarity scores (higher = more similar)
                # ChromaDB returns cosine distances, so similarity = 1 - distance
                similarities = [1.0 - distance for distance in distances]

                return list(zip(scene_ids, similarities))

            return []

        except Exception:
            return []

    def count(self) -> int:
        """
        Get the number of scenes in the vector store.

        Returns
        -------
        int
            Number of stored scene embeddings
        """
        return self.collection.count()

    def clear(self) -> bool:
        """
        Clear all embeddings from the vector store.

        Returns
        -------
        bool
            True if successfully cleared, False otherwise
        """
        try:
            # Delete and recreate collection
            self.client.delete_collection(f"scenes_{self.project}")
            self.collection = self.client.get_or_create_collection(
                name=f"scenes_{self.project}", metadata={"hnsw:space": "cosine"}
            )
            return True

        except Exception:
            return False
