"""
foreshadow_scheduler.py

Foreshadow Scheduler for Final Engine - manages story foreshadowing elements.

Functions:
- schedule_foreshadow(hint: str, introduced_ep: int) -> dict: Adds new foreshadow
- track_payoff(episode: int, content: str) -> bool: Checks for foreshadow resolution

Schema for foreshadow.json:
{
  "foreshadows": [
    {
      "id": "f001",
      "hint": "신비한 검의 존재",
      "introduced": 5,
      "due": 25,
      "payoff": null
    }
  ]
}
"""

import json
import os
import random
import re
import uuid
from typing import Dict, List
from src.utils.path_helper import data_path


# Default total episodes for due calculation
TOTAL_EPISODES = 250


def _get_foreshadow_file_path(project: str = "default") -> str:
    """Get the path to the foreshadow.json file."""
    return str(data_path("foreshadow.json", project))


def _load_foreshadows(project: str = "default") -> Dict:
    """
    Load foreshadows from the JSON file.

    Parameters
    ----------
    project : str, optional
        Project ID for path resolution, defaults to "default"

    Returns
    -------
    Dict
        Dictionary containing foreshadows data
    """
    file_path = _get_foreshadow_file_path(project)

    if not os.path.exists(file_path):
        # Create empty structure if file doesn't exist
        return {"foreshadows": []}

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        # Return empty structure if file is corrupted or unreadable
        return {"foreshadows": []}


def _save_foreshadows(data: Dict, project: str = "default") -> None:
    """
    Save foreshadows to the JSON file.

    Parameters
    ----------
    data : Dict
        Dictionary containing foreshadows data
    project : str, optional
        Project ID for path resolution, defaults to "default"
    """
    file_path = _get_foreshadow_file_path(project)

    # Ensure directory exists
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _generate_unique_id(existing_ids: List[str]) -> str:
    """
    Generate a unique foreshadow ID.

    Parameters
    ----------
    existing_ids : List[str]
        List of existing foreshadow IDs

    Returns
    -------
    str
        Unique ID in format f{uuid[:6]}
    """
    max_attempts = 100

    for _ in range(max_attempts):
        # Generate ID using first 6 characters of UUID
        new_id = f"f{str(uuid.uuid4()).replace('-', '')[:6]}"

        if new_id not in existing_ids:
            return new_id

    # Fallback to timestamp-based ID if UUID approach fails
    import time

    timestamp_id = f"f{int(time.time() * 1000) % 1000000:06d}"
    return timestamp_id


def _calculate_due_episode(
    introduced_ep: int, total_episodes: int = TOTAL_EPISODES
) -> int:
    """
    Calculate due episode for foreshadow resolution.

    Parameters
    ----------
    introduced_ep : int
        Episode where foreshadow was introduced
    total_episodes : int, optional
        Total number of episodes in the story

    Returns
    -------
    int
        Due episode number
    """
    # Calculate due as introduced + random(10, 30), capped at total episodes
    random_offset = random.randint(10, 30)
    due_episode = introduced_ep + random_offset

    return min(due_episode, total_episodes)


def schedule_foreshadow(
    hint: str, introduced_ep: int, project: str = "default"
) -> dict:
    """
    Schedule a new foreshadow element.

    Parameters
    ----------
    hint : str
        Description of the foreshadow hint
    introduced_ep : int
        Episode number where the foreshadow is introduced
    project : str, optional
        Project ID for path resolution, defaults to "default"

    Returns
    -------
    dict
        Created foreshadow record with id, hint, introduced, due, and payoff fields
    """
    # Load existing foreshadows
    data = _load_foreshadows(project)

    # Get existing IDs for uniqueness check
    existing_ids = [f["id"] for f in data["foreshadows"]]

    # Generate unique ID
    foreshadow_id = _generate_unique_id(existing_ids)

    # Calculate due episode
    due_episode = _calculate_due_episode(introduced_ep)

    # Create foreshadow record
    foreshadow = {
        "id": foreshadow_id,
        "hint": hint,
        "introduced": introduced_ep,
        "due": due_episode,
        "payoff": None,
    }

    # Add to data and save
    data["foreshadows"].append(foreshadow)
    _save_foreshadows(data, project)

    return foreshadow


def track_payoff(episode: int, content: str, project: str = "default") -> bool:
    """
    Track foreshadow payoff by looking for resolution patterns in content.

    Looks for patterns like [RESOLVED:f001abc] in the content and marks
    the corresponding foreshadow as resolved.

    Parameters
    ----------
    episode : int
        Current episode number
    content : str
        Episode content to analyze for resolution patterns
    project : str, optional
        Project ID for path resolution, defaults to "default"

    Returns
    -------
    bool
        True if any foreshadows were resolved, False otherwise
    """
    # Load existing foreshadows
    data = _load_foreshadows(project)

    # Pattern to match [RESOLVED:{id}]
    pattern = r"\[RESOLVED:([^\]]+)\]"
    matches = re.findall(pattern, content)

    if not matches:
        return False

    resolved_any = False

    # Check each foreshadow for resolution
    for foreshadow in data["foreshadows"]:
        if foreshadow["id"] in matches and foreshadow["payoff"] is None:
            # Mark as resolved
            foreshadow["payoff"] = episode
            resolved_any = True

    # Save updated data if any resolutions were found
    if resolved_any:
        _save_foreshadows(data, project)

    return resolved_any


def get_foreshadows(project: str = "default") -> List[dict]:
    """
    Get all foreshadows.

    Parameters
    ----------
    project : str, optional
        Project ID for path resolution, defaults to "default"

    Returns
    -------
    List[dict]
        List of all foreshadow records
    """
    data = _load_foreshadows(project)
    return data["foreshadows"]


def get_unresolved_foreshadows(project: str = "default") -> List[dict]:
    """
    Get all unresolved foreshadows.

    Parameters
    ----------
    project : str, optional
        Project ID for path resolution, defaults to "default"

    Returns
    -------
    List[dict]
        List of foreshadow records where payoff is None
    """
    data = _load_foreshadows(project)
    return [f for f in data["foreshadows"] if f["payoff"] is None]


def get_overdue_foreshadows(
    current_episode: int, project: str = "default"
) -> List[dict]:
    """
    Get foreshadows that are overdue for resolution.

    Parameters
    ----------
    current_episode : int
        Current episode number
    project : str, optional
        Project ID for path resolution, defaults to "default"

    Returns
    -------
    List[dict]
        List of foreshadow records that are past their due episode and unresolved
    """
    unresolved = get_unresolved_foreshadows(project)
    return [f for f in unresolved if current_episode > f["due"]]
