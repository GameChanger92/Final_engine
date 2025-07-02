"""
schedule_guard.py

Schedule Guard for Final Engine - checks foreshadow resolution compliance.

Monitors foreshadows that are past their due episode without resolution (payoff=null).
Raises RetryException when overdue foreshadows are detected.
"""

from src.core.guard_registry import BaseGuard, register_guard
from src.exceptions import RetryException
from src.plugins.foreshadow_scheduler import (
    _load_foreshadows,
    _save_foreshadows,
    get_overdue_foreshadows,
)


@register_guard(order=3)
class ScheduleGuard(BaseGuard):
    """
    Guard that checks foreshadow resolution compliance.

    Ensures that foreshadows are resolved by their due episode.
    """

    def check(self, current_episode: int) -> dict[str, any]:
        """
        Check for overdue foreshadows that need resolution.

        Parameters
        ----------
        current_episode : int
            Current episode number to check against

        Returns
        -------
        Dict[str, any]
            Results containing overdue foreshadows and flags

        Raises
        ------
        RetryException
            If any foreshadows are past their due episode without resolution
        """
        results = {
            "current_episode": current_episode,
            "overdue_foreshadows": [],
            "flags": {},
            "passed": True,
        }

        # Get overdue foreshadows
        overdue = get_overdue_foreshadows(current_episode)
        results["overdue_foreshadows"] = overdue

        # Check if any are overdue
        flags = {}
        if overdue:
            overdue_details = []
            for foreshadow in overdue:
                detail = {
                    "id": foreshadow["id"],
                    "hint": foreshadow["hint"],
                    "introduced": foreshadow["introduced"],
                    "due": foreshadow["due"],
                    "episodes_overdue": current_episode - foreshadow["due"],
                }
                overdue_details.append(detail)

            flags["overdue_foreshadows"] = {
                "count": len(overdue),
                "details": overdue_details,
                "message": f"{len(overdue)} foreshadow(s) past due episode without resolution",
            }

        results["flags"] = flags

        if flags:
            results["passed"] = False
            # Create error message
            flag_messages = [flag_data["message"] for flag_data in flags.values()]
            error_message = "Foreshadow schedule violations: " + "; ".join(flag_messages)

            raise RetryException(message=error_message, flags=flags, guard_name="schedule_guard")

        return results

    def update_payoff(self, foreshadow_id: str, episode: int) -> bool:
        """
        Update foreshadow payoff (mark as resolved).

        Parameters
        ----------
        foreshadow_id : str
            ID of the foreshadow to resolve
        episode : int
            Episode number where the foreshadow was resolved

        Returns
        -------
        bool
            True if foreshadow was found and updated, False otherwise
        """
        # Load existing foreshadows
        data = _load_foreshadows()

        # Find the foreshadow by ID
        for foreshadow in data["foreshadows"]:
            if foreshadow["id"] == foreshadow_id:
                # Only update if not already resolved
                if foreshadow["payoff"] is None:
                    foreshadow["payoff"] = episode
                    _save_foreshadows(data)
                    return True
                else:
                    # Already resolved
                    return False

        # Foreshadow not found
        return False


def check_schedule_guard(current_episode: int) -> dict[str, any]:
    """
    Run schedule guard checks for the given episode.

    Parameters
    ----------
    current_episode : int
        Current episode number

    Returns
    -------
    Dict[str, any]
        Results containing schedule guard check results

    Raises
    ------
    RetryException
        If any foreshadows are overdue for resolution
    """
    guard = ScheduleGuard()
    return guard.check(current_episode)


def schedule_guard(current_episode: int) -> bool:
    """
    Main entry point for schedule guard check.

    Parameters
    ----------
    current_episode : int
        Current episode number

    Returns
    -------
    bool
        True if no schedule violations detected

    Raises
    ------
    RetryException
        If any foreshadows are overdue for resolution
    """
    try:
        check_schedule_guard(current_episode)
        return True
    except RetryException:
        # Re-raise the exception to be handled by the caller
        raise
