"""
date_guard.py

Date Guard for Final Engine - monitors story chronological progression.

Ensures that episode dates don't move backwards in time, maintaining
chronological consistency in the story timeline.
"""

import json
import os
from datetime import datetime
from typing import Any

from src.core.guard_registry import BaseGuard, register_guard
from src.exceptions import RetryException
from src.utils.path_helper import data_path


@register_guard(order=5)
class DateGuard(BaseGuard):
    """
    Guard that monitors chronological date progression.

    Tracks episode dates and ensures they don't go backwards in time.
    """

    def __init__(self, *args, project="default", **kwargs):
        """
        Initialize DateGuard.

        Parameters
        ----------
        date_log_path : str, optional
            Path to the file storing episode dates.
            If None, uses default path for the project.
        project : str, optional
            Project ID for path resolution, defaults to "default"
        """
        # Handle backward compatibility for date_log_path parameter
        date_log_path = None
        if args:
            date_log_path = args[0]
        elif "date_log_path" in kwargs:
            date_log_path = kwargs.pop("date_log_path")

        self.project = project
        if date_log_path is None:
            self.date_log_path = data_path("episode_dates.json", project)
        else:
            self.date_log_path = date_log_path

    def _load_date_log(self) -> dict[int, str]:
        """
        Load episode date log.

        Returns
        -------
        Dict[int, str]
            Dictionary mapping episode numbers to dates
        """
        try:
            with open(self.date_log_path, encoding="utf-8") as f:
                data = json.load(f)
                # Convert string keys back to integers
                return {int(k): v for k, v in data.items()}
        except FileNotFoundError:
            return {}
        except json.JSONDecodeError:
            return {}
        except ValueError:
            return {}

    def _save_date_log(self, date_log: dict[int, str]) -> None:
        """
        Save episode date log to disk.

        Parameters
        ----------
        date_log : Dict[int, str]
            Episode date mapping to save
        """
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.date_log_path), exist_ok=True)

        # Convert integer keys to strings for JSON
        string_log = {str(k): v for k, v in date_log.items()}

        with open(self.date_log_path, "w", encoding="utf-8") as f:
            json.dump(string_log, f, ensure_ascii=False, indent=2)

    def _parse_date(self, date_str: str) -> datetime | None:
        """
        Parse date string to datetime object.

        Parameters
        ----------
        date_str : str
            Date string in YYYY-MM-DD format

        Returns
        -------
        Optional[datetime]
            Parsed datetime object, or None if parsing fails
        """
        if not date_str:
            return None

        try:
            return datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            try:
                # Try alternative formats
                return datetime.strptime(date_str, "%Y/%m/%d")
            except ValueError:
                return None

    def _extract_episode_date(self, context: dict[str, Any], episode_num: int) -> str | None:
        """
        Extract date from context or metadata.

        Parameters
        ----------
        context : Dict[str, Any]
            Episode context data
        episode_num : int
            Episode number

        Returns
        -------
        Optional[str]
            Date string if found, None otherwise
        """
        # Try to get date from context["date"]
        if isinstance(context, dict) and "date" in context:
            return context["date"]

        # Try to get date from .meta["date"]
        if isinstance(context, dict) and "meta" in context:
            meta = context["meta"]
            if isinstance(meta, dict) and "date" in meta:
                return meta["date"]

        # Try to get date from episode_date key
        if isinstance(context, dict) and "episode_date" in context:
            return context["episode_date"]

        return None

    def check(self, context: dict[str, Any], episode_num: int) -> dict[str, Any]:
        """
        Check for date progression violations.

        Parameters
        ----------
        context : Dict[str, Any]
            Episode context or data containing date information
        episode_num : int
            Current episode number

        Returns
        -------
        Dict[str, Any]
            Check results with flags and violations

        Raises
        ------
        RetryException
            If date goes backwards from previous episode
        """
        results = {
            "current_episode": episode_num,
            "current_date": None,
            "previous_date": None,
            "previous_episode": None,
            "flags": {},
            "passed": True,
            "date_log_created": False,
        }

        # Extract current episode date
        current_date_str = self._extract_episode_date(context, episode_num)

        if not current_date_str:
            # No date found in context - this is allowed for now
            results["passed"] = True
            return results

        results["current_date"] = current_date_str

        # Parse current date
        current_date = self._parse_date(current_date_str)
        if not current_date:
            # Invalid date format - not our concern, let other systems handle it
            return results

        # Load existing date log
        date_log = self._load_date_log()

        if not date_log:
            # First episode or no previous dates - create log and pass
            date_log[episode_num] = current_date_str
            self._save_date_log(date_log)
            results["date_log_created"] = True
            return results

        # Find the most recent previous episode
        previous_episodes = [ep for ep in date_log.keys() if ep < episode_num]

        if not previous_episodes:
            # No previous episodes - update log and pass
            date_log[episode_num] = current_date_str
            self._save_date_log(date_log)
            return results

        # Get the most recent previous episode
        previous_episode = max(previous_episodes)
        previous_date_str = date_log[previous_episode]
        results["previous_episode"] = previous_episode
        results["previous_date"] = previous_date_str

        # Parse previous date
        previous_date = self._parse_date(previous_date_str)
        if not previous_date:
            # Previous date is invalid - update log and pass
            date_log[episode_num] = current_date_str
            self._save_date_log(date_log)
            return results

        # Check if current date is before previous date
        if current_date < previous_date:
            results["passed"] = False

            # Create flags
            days_backward = (previous_date - current_date).days
            flags = {
                "date_backstep": {
                    "current_date": current_date_str,
                    "previous_date": previous_date_str,
                    "current_episode": episode_num,
                    "previous_episode": previous_episode,
                    "days_backward": days_backward,
                    "message": f"Episode {episode_num} date {current_date_str} is {days_backward} days before episode {previous_episode} date {previous_date_str}",
                }
            }
            results["flags"] = flags

            error_message = f"Date backstep: Episode {episode_num} ({current_date_str}) goes back {days_backward} days from Episode {previous_episode} ({previous_date_str})"

            raise RetryException(message=error_message, flags=flags, guard_name="date_guard")

        # Date is valid - update log
        date_log[episode_num] = current_date_str
        self._save_date_log(date_log)

        return results


def check_date_guard(
    context: dict[str, Any], episode_num: int, project: str = "default"
) -> dict[str, Any]:
    """
    Check date guard with current episode context and number.

    Parameters
    ----------
    context : Dict[str, Any]
        Episode context data
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
        If date progression violations are detected
    """
    guard = DateGuard(project=project)
    return guard.check(context, episode_num)


def date_guard(context: dict[str, Any], episode_num: int, project: str = "default") -> bool:
    """
    Main entry point for date guard check.

    Parameters
    ----------
    context : Dict[str, Any]
        Episode context data containing date information
    episode_num : int
        Current episode number
    project : str, optional
        Project ID for path resolution, defaults to "default"

    Returns
    -------
    bool
        True if date progression is valid

    Raises
    ------
    RetryException
        If date progression violations are detected
    """
    try:
        check_date_guard(context, episode_num, project)
        return True
    except RetryException:
        # Re-raise the exception to be handled by the caller
        raise
