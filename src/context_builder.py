"""
context_builder.py

Enhanced context builder for Final Engine.
Combines knowledge graphs, vector search results, and style configurations
into a final prompt string using Jinja2 templates.
"""

import json
import logging
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from src.embedding.vector_store import VectorStore
from src.utils.path_helper import data_path

logger = logging.getLogger(__name__)


class ContextBuilder:
    """
    Enhanced context builder that combines multiple data sources
    into a formatted context string for LLM consumption.
    """

    def __init__(self, project: str = "default"):
        """
        Initialize ContextBuilder for a specific project.

        Parameters
        ----------
        project : str, optional
            Project ID for path resolution, defaults to "default"
        """
        self.project = project
        self.vector_store = VectorStore(project)

        # Setup Jinja2 environment
        template_dir = Path(__file__).parent.parent / "templates"
        self.jinja_env = Environment(loader=FileSystemLoader(str(template_dir)))

    def load_knowledge_graph(self) -> dict[str, Any]:
        """
        Load knowledge graph from projects/{id}/data/knowledge_graph.json.

        Returns
        -------
        Dict[str, Any]
            Knowledge graph data or empty dict if not found
        """
        try:
            kg_path = data_path("knowledge_graph.json", self.project)
            if not kg_path.exists():
                logger.warning(f"Knowledge graph not found: {kg_path}")
                return {}

            with open(kg_path, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logger.error(f"Error loading knowledge graph: {e}")
            return {}

    def load_style_config(self) -> dict[str, Any]:
        """
        Load style configuration from projects/{id}/data/style_config.json.

        Returns
        -------
        Dict[str, Any]
            Style configuration or default values if not found
        """
        try:
            style_path = data_path("style_config.json", self.project)
            if not style_path.exists():
                logger.warning(f"Style config not found: {style_path}")
                return {
                    "platform": "default",
                    "style": {"tone": "neutral", "voice": "3rd_person"},
                    "word_count_target": 2000,
                }

            with open(style_path, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logger.error(f"Error loading style config: {e}")
            return {
                "platform": "default",
                "style": {"tone": "neutral", "voice": "3rd_person"},
                "word_count_target": 2000,
            }

    def get_similar_scenes(self, scene_text: str, top_k: int = 5) -> list[tuple[str, float]]:
        """
        Get similar scenes using vector search.

        Parameters
        ----------
        scene_text : str
            Scene text to find similar scenes for
        top_k : int, optional
            Number of similar scenes to return, defaults to 5

        Returns
        -------
        List[Tuple[str, float]]
            List of (scene_id, similarity_score) tuples
        """
        if not scene_text or not scene_text.strip():
            return []

        try:
            return self.vector_store.similar(scene_text, top_k=top_k)
        except Exception as e:
            logger.error(f"Error in vector search: {e}")
            return []

    def build_context(
        self,
        scenes: list[str],
        previous_episode: str | None = None,
        scene_text_for_vector: str | None = None,
    ) -> str:
        """
        Build complete context string using Jinja2 template.

        Parameters
        ----------
        scenes : List[str]
            List of scene descriptions
        previous_episode : Optional[str], optional
            Previous episode summary, by default None
        scene_text_for_vector : Optional[str], optional
            Text to use for vector similarity search, by default None
            If None, uses the first scene from scenes list

        Returns
        -------
        str
            Formatted context string ready for LLM consumption
        """
        # Load data sources
        knowledge_graph = self.load_knowledge_graph()
        style_config = self.load_style_config()

        # Get vector search results
        vector_text = scene_text_for_vector or (scenes[0] if scenes else "")
        similar_scenes = self.get_similar_scenes(vector_text, top_k=5)

        # Log vector search results
        if similar_scenes:
            logger.info(f"Context built with {len(similar_scenes)} similar scenes")

        # Prepare template context
        template_context = {
            "characters": knowledge_graph.get("characters", {}),
            "story_elements": knowledge_graph.get("story_elements", {}),
            "previous_episode": previous_episode,
            "similar_scenes": similar_scenes,
            "style": style_config,
            "scenes": scenes,
        }

        # Render template
        try:
            template = self.jinja_env.get_template("context_prompt.j2")
            return template.render(**template_context)
        except TemplateNotFound:
            logger.error("Template context_prompt.j2 not found")
            # Fallback to simple format
            return self._fallback_context(scenes, similar_scenes)
        except Exception as e:
            logger.error(f"Error rendering template: {e}")
            return self._fallback_context(scenes, similar_scenes)

    def _fallback_context(self, scenes: list[str], similar_scenes: list[tuple[str, float]]) -> str:
        """
        Fallback context generation when template fails.

        Parameters
        ----------
        scenes : List[str]
            List of scene descriptions
        similar_scenes : List[Tuple[str, float]]
            List of similar scenes from vector search

        Returns
        -------
        str
            Simple formatted context string
        """
        context_parts = [
            "[Character Info: TO BE ADDED]",
            "[Previous Episode: TO BE ADDED]",
        ]

        if similar_scenes:
            context_parts.append("Vector Search Results:")
            for scene_id, score in similar_scenes:
                context_parts.append(f"- {scene_id} (similarity: {score:.2f})")
        else:
            context_parts.append("[Vector Search: TO BE ADDED]")

        context_parts.append("")  # Empty line separator

        # Add numbered scenes
        for i, scene in enumerate(scenes, 1):
            context_parts.append(f"{i}. {scene}")

        return "\n".join(context_parts)


# Backward compatibility function
def make_context(scenes: list[str]) -> str:
    """
    Backward compatibility function for existing code.

    Parameters
    ----------
    scenes : List[str]
        List of scene descriptions

    Returns
    -------
    str
        Formatted context string
    """
    builder = ContextBuilder()
    return builder.build_context(scenes)
