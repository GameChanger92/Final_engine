"""
relation_guard.py

Relation Guard for Final Engine - detects sudden relationship changes.

Monitors relation_matrix.json for character relationship changes between episodes
and raises RetryException if relationships flip too quickly (within tolerance_ep).
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from src.exceptions import RetryException
from src.utils.path_helper import data_path
from src.core.guard_registry import BaseGuard, register_guard


@register_guard(order=8)
class RelationGuard(BaseGuard):
    """
    Relation Guard - validates character relationships don't change too abruptly.

    Checks character relationships across episodes and raises RetryException
    if relationships flip from opposing states (친구 ↔ 적) within tolerance window.
    """

    def __init__(
        self, relation_path: str = None, project: str = "default", tolerance_ep: int = 3
    ):
        """
        Initialize RelationGuard with relation matrix file path.

        Parameters
        ----------
        relation_path : str, optional
            Path to relation_matrix.json file containing episode relationships.
            If None, uses default path for the project.
        project : str, optional
            Project ID for path resolution, defaults to "default"
        tolerance_ep : int, optional
            Number of episodes tolerance for relationship changes, defaults to 3
        """
        if relation_path is None:
            self.relation_path = data_path("relation_matrix.json", project)
        else:
            self.relation_path = Path(relation_path)
        self.project = project
        self.tolerance_ep = tolerance_ep
        self.relations = self._load_relations()

    def _load_relations(self) -> List[Dict[str, Any]]:
        """
        Load relations from JSON file.

        Returns
        -------
        List[Dict[str, Any]]
            List of episode relation dictionaries with ep and relations fields

        Raises
        ------
        FileNotFoundError
            If relation matrix file doesn't exist
        json.JSONDecodeError
            If relation matrix file is invalid JSON
        """
        try:
            with open(self.relation_path, "r", encoding="utf-8") as f:
                relations = json.load(f)
                if not isinstance(relations, list):
                    # Return empty list on invalid structure (graceful handling)
                    return []
                return relations
        except (FileNotFoundError, OSError):
            # Return empty list on file errors (graceful handling)
            return []
        except (json.JSONDecodeError, ValueError):
            # Return empty list on JSON parsing errors (graceful handling)
            return []

    def _is_opposing_relation(self, rel1: str, rel2: str) -> bool:
        """
        Check if two relationships are opposing (친구 ↔ 적).

        Parameters
        ----------
        rel1 : str
            First relationship type
        rel2 : str
            Second relationship type

        Returns
        -------
        bool
            True if relationships are opposing
        """
        opposing_pairs = [
            ("친구", "적"),
            ("적", "친구"),
        ]
        return (rel1, rel2) in opposing_pairs

    def _find_relation_at_episode(self, char_pair: str, episode: int) -> Optional[str]:
        """
        Find relationship between character pair at specific episode.

        Parameters
        ----------
        char_pair : str
            Character pair in format "A,B"
        episode : int
            Episode number to check

        Returns
        -------
        Optional[str]
            Relationship type if found, None otherwise
        """
        # Sort the pair to handle both "A,B" and "B,A" formats
        chars = sorted(char_pair.split(","))
        normalized_pair = ",".join(chars)

        # Find the most recent episode <= target episode with this relationship
        best_episode = -1
        best_relation = None

        for ep_data in self.relations:
            ep_num = ep_data.get("ep", 0)
            if ep_num <= episode:
                relations = ep_data.get("relations", {})
                # Check both orderings of the character pair
                if char_pair in relations:
                    if ep_num > best_episode:
                        best_episode = ep_num
                        best_relation = relations[char_pair]
                elif normalized_pair in relations:
                    if ep_num > best_episode:
                        best_episode = ep_num
                        best_relation = relations[normalized_pair]
                else:
                    # Check reverse order
                    reverse_pair = ",".join(reversed(chars))
                    if reverse_pair in relations:
                        if ep_num > best_episode:
                            best_episode = ep_num
                            best_relation = relations[reverse_pair]

        return best_relation

    def check(self, episode_num: int) -> Dict[str, Any]:
        """
        Check for relationship violations at given episode.

        Parameters
        ----------
        episode_num : int
            Current episode number to check

        Returns
        -------
        Dict[str, Any]
            Results dictionary with passed status and violation details

        Raises
        ------
        RetryException
            If relationship changes too quickly within tolerance window
        """
        results = {
            "passed": True,
            "violations": [],
            "episode": episode_num,
            "tolerance_ep": self.tolerance_ep,
        }

        # Find current episode relations
        current_relations = {}
        for ep_data in self.relations:
            if ep_data.get("ep") == episode_num:
                current_relations = ep_data.get("relations", {})
                break

        if not current_relations:
            # No relations defined for this episode - pass
            return results

        # Check each relationship for rapid changes
        for char_pair, current_relation in current_relations.items():
            # Find the most recent previous episode with data for this character pair
            most_recent_ep = -1
            most_recent_relation = None

            for ep_data in self.relations:
                ep_num = ep_data.get("ep", 0)
                if ep_num < episode_num:  # Only consider previous episodes
                    relations = ep_data.get("relations", {})
                    # Check if this episode has data for our character pair (both orderings)
                    chars = sorted(char_pair.split(","))
                    normalized_pair = ",".join(chars)
                    reverse_pair = ",".join(reversed(chars))

                    found_relation = None
                    if char_pair in relations:
                        found_relation = relations[char_pair]
                    elif normalized_pair in relations:
                        found_relation = relations[normalized_pair]
                    elif reverse_pair in relations:
                        found_relation = relations[reverse_pair]

                    if found_relation and ep_num > most_recent_ep:
                        most_recent_ep = ep_num
                        most_recent_relation = found_relation

            # Check if the most recent relationship is opposing and within tolerance
            if most_recent_relation and most_recent_ep > 0:
                episode_gap = episode_num - most_recent_ep
                if episode_gap > self.tolerance_ep and self._is_opposing_relation(
                    most_recent_relation, current_relation
                ):
                    # Found opposing relationship beyond tolerance window
                    violation = {
                        "char_pair": char_pair,
                        "previous_episode": most_recent_ep,
                        "previous_relation": most_recent_relation,
                        "current_episode": episode_num,
                        "current_relation": current_relation,
                        "episode_gap": episode_gap,
                        "tolerance_ep": self.tolerance_ep,
                        "message": f"Relationship {char_pair} changed from '{most_recent_relation}' to '{current_relation}' between episodes {most_recent_ep} and {episode_num} (gap: {episode_gap}, tolerance: {self.tolerance_ep})",
                    }

                    results["passed"] = False
                    results["violations"].append(violation)

                    # Create flags for RetryException
                    flags = {
                        "relation_violation": {
                            "char_pair": char_pair,
                            "previous_episode": most_recent_ep,
                            "previous_relation": most_recent_relation,
                            "current_episode": episode_num,
                            "current_relation": current_relation,
                            "episode_gap": episode_gap,
                            "tolerance_ep": self.tolerance_ep,
                        }
                    }
                    results["flags"] = flags

                    # Raise exception on first violation (as per spec)
                    raise RetryException(
                        message=violation["message"],
                        flags=flags,
                        guard_name="relation_guard",
                    )

        return results


def check_relation_guard(
    episode_num: int,
    relation_path: str = None,
    project: str = "default",
    tolerance_ep: int = 3,
) -> Dict[str, Any]:
    """
    Check relation guard for specific episode.

    Parameters
    ----------
    episode_num : int
        Episode number to check
    relation_path : str, optional
        Path to relation_matrix.json file.
        If None, uses default path for the project.
    project : str, optional
        Project ID for path resolution, defaults to "default"
    tolerance_ep : int, optional
        Number of episodes tolerance for relationship changes, defaults to 3

    Returns
    -------
    Dict[str, Any]
        Results dictionary with passed status and violation details

    Raises
    ------
    RetryException
        If relationship changes too quickly within tolerance window
    """
    guard = RelationGuard(relation_path, project, tolerance_ep)
    return guard.check(episode_num)


def relation_guard(
    episode_num: int,
    relation_path: str = None,
    project: str = "default",
    tolerance_ep: int = 3,
) -> bool:
    """
    Main entry point for relation guard check.

    Parameters
    ----------
    episode_num : int
        Episode number to check
    relation_path : str, optional
        Path to relation_matrix.json file.
        If None, uses default path for the project.
    project : str, optional
        Project ID for path resolution, defaults to "default"
    tolerance_ep : int, optional
        Number of episodes tolerance for relationship changes, defaults to 3

    Returns
    -------
    bool
        True if relationships pass all checks

    Raises
    ------
    RetryException
        If relationship changes too quickly within tolerance window
    """
    try:
        check_relation_guard(episode_num, relation_path, project, tolerance_ep)
        return True
    except RetryException:
        # Re-raise the exception to be handled by the caller
        raise
