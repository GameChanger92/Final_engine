"""
anchor_guard.py

Anchor Guard for Final Engine - validates anchor events appear within expected episodes.

Monitors anchors.json for core story events and ensures they appear within
the specified episode range (anchor_ep ± 1). Raises RetryException if
anchor events are missing from expected episodes.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any
from src.exceptions import RetryException
from src.utils.path_helper import data_path


class AnchorGuard:
    """
    Anchor Guard - validates anchor events appear within expected episodes.

    Checks that anchor events defined in anchors.json appear within the
    specified episode range (anchor_ep ± 1).
    """

    def __init__(self, *args, project="default", **kwargs):
        """
        Initialize AnchorGuard with anchors file path.

        Parameters
        ----------
        anchors_path : str, optional
            Path to anchors.json file containing anchor events.
            If None, uses default path for the project.
        project : str, optional
            Project ID for path resolution, defaults to "default"
        """
        # Handle backward compatibility for anchors_path parameter
        anchors_path = None
        if args:
            anchors_path = args[0]
        elif "anchors_path" in kwargs:
            anchors_path = kwargs.pop("anchors_path")

        self.project = project
        if anchors_path is None:
            self.anchors_path = data_path("anchors.json", project)
        else:
            self.anchors_path = Path(anchors_path)
        self.anchors = self._load_anchors()

    def _load_anchors(self) -> List[Dict[str, Any]]:
        """
        Load anchors from JSON file.

        Returns
        -------
        List[Dict[str, Any]]
            List of anchor dictionaries with id, goal, anchor_ep fields

        Raises
        ------
        FileNotFoundError
            If anchors file doesn't exist
        json.JSONDecodeError
            If anchors file is invalid JSON
        """
        try:
            with open(self.anchors_path, "r", encoding="utf-8") as f:
                anchors = json.load(f)
                if not isinstance(anchors, list):
                    raise ValueError(
                        "anchors.json must contain a list of anchor objects"
                    )
                return anchors
        except FileNotFoundError:
            # Return empty list if no anchors file exists
            return []

    def _is_episode_in_range(self, episode_num: int, anchor_ep: int) -> bool:
        """
        Check if episode number is within anchor episode range (±1).

        Parameters
        ----------
        episode_num : int
            Current episode number
        anchor_ep : int
            Target anchor episode number

        Returns
        -------
        bool
            True if episode is within anchor_ep ± 1 range
        """
        return abs(episode_num - anchor_ep) <= 1

    def _extract_keywords_from_goal(self, goal: str) -> List[str]:
        """
        Extract meaningful keywords from anchor goal for searching.

        Parameters
        ----------
        goal : str
            Anchor goal description

        Returns
        -------
        List[str]
            List of keywords to search for
        """
        # Remove common stop words and extract meaningful terms
        stop_words = {
            "이",
            "가",
            "를",
            "을",
            "의",
            "에",
            "와",
            "과",
            "로",
            "으로",
            "는",
            "은",
            "한다",
            "다",
            "고",
            "도",
        }

        # Split goal into words and filter out stop words and short words
        words = re.findall(r"\b\w+\b", goal)

        # Remove Korean particles and suffixes to extract root words
        cleaned_words = []
        for word in words:
            # Remove common Korean particles/suffixes
            cleaned_word = re.sub(
                r"(이|가|를|을|의|에|와|과|로|으로|는|은|다)$", "", word
            )
            if len(cleaned_word) >= 2 and cleaned_word not in stop_words:
                cleaned_words.append(cleaned_word)

        # If no meaningful keywords found, use the whole goal
        if not cleaned_words:
            cleaned_words = [goal]

        return cleaned_words

    def _search_keywords_in_content(self, content: str, keywords: List[str]) -> bool:
        """
        Search for keywords in episode content.

        Parameters
        ----------
        content : str
            Episode content to search in
        keywords : List[str]
            Keywords to search for

        Returns
        -------
        bool
            True if any keyword is found in content
        """
        if not content:
            return False

        content_lower = content.lower()

        # Check if any keyword appears in the content
        for keyword in keywords:
            if keyword.lower() in content_lower:
                return True

        return False

    def check(self, episode_content: str, episode_num: int) -> Dict[str, Any]:
        """
        Check anchor compliance for the given episode.

        Parameters
        ----------
        episode_content : str
            Content of the current episode
        episode_num : int
            Current episode number

        Returns
        -------
        Dict[str, Any]
            Check results with status and details

        Raises
        ------
        RetryException
            If anchor events are missing from expected episodes
        """
        results = {
            "passed": True,
            "episode_num": episode_num,
            "anchors_checked": [],
            "missing_anchors": [],
        }

        # Check each anchor
        for anchor in self.anchors:
            anchor_id = anchor.get("id", "unknown")
            goal = anchor.get("goal", "")
            anchor_ep = anchor.get("anchor_ep")

            # Skip anchors with missing required fields
            if anchor_ep is None or not goal:
                continue

            # Only check anchors that should appear in this episode range
            if self._is_episode_in_range(episode_num, anchor_ep):
                keywords = self._extract_keywords_from_goal(goal)
                found = self._search_keywords_in_content(episode_content, keywords)

                anchor_check = {
                    "id": anchor_id,
                    "goal": goal,
                    "anchor_ep": anchor_ep,
                    "keywords": keywords,
                    "found": found,
                }

                results["anchors_checked"].append(anchor_check)

                if not found:
                    results["missing_anchors"].append(anchor_check)
                    results["passed"] = False

        # If any anchors are missing, raise RetryException
        if not results["passed"]:
            missing_details = []
            for missing in results["missing_anchors"]:
                missing_details.append(
                    f"'{missing['goal']}' (anchor_ep {missing['anchor_ep']}, keywords: {missing['keywords']})"
                )

            flags = {
                "anchor_compliance": {
                    "episode_num": episode_num,
                    "missing_anchors": results["missing_anchors"],
                    "total_checked": len(results["anchors_checked"]),
                }
            }

            error_message = (
                f"Anchor compliance failure in episode {episode_num}: "
                f"Missing {len(results['missing_anchors'])} required anchor event(s): "
                f"{', '.join(missing_details)}"
            )

            raise RetryException(
                message=error_message, flags=flags, guard_name="anchor_guard"
            )

        return results


def check_anchor_guard(
    episode_content: str, episode_num: int, project: str = "default"
) -> Dict[str, Any]:
    """
    Check anchor guard with episode content and number.

    Parameters
    ----------
    episode_content : str
        Content of the episode to check
    episode_num : int
        Current episode number
    project : str, optional
        Project ID for path resolution, defaults to "default"

    Returns
    -------
    Dict[str, Any]
        Check results

    Raises
    ------
    RetryException
        If anchor compliance violations are detected
    """
    guard = AnchorGuard(project=project)
    return guard.check(episode_content, episode_num)


def anchor_guard(
    episode_content: str, episode_num: int, project: str = "default"
) -> None:
    """
    Main anchor guard function - validates anchor events in episode content.

    Parameters
    ----------
    episode_content : str
        Content of the episode to check
    episode_num : int
        Current episode number
    project : str, optional
        Project ID for path resolution, defaults to "default"

    Raises
    ------
    RetryException
        If anchor compliance violations are detected
    """
    check_anchor_guard(episode_content, episode_num, project)
