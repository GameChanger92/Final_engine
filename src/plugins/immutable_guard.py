"""
immutable_guard.py

Immutable Guard for Final Engine - monitors immutable character fields.

Detects changes to fields marked as immutable in characters.json and raises
RetryException when violations are detected.
"""

import json
import os
from typing import Dict, Any
from src.exceptions import RetryException
from src.utils.path_helper import data_path


class ImmutableGuard:
    """
    Guard that monitors immutable character fields.

    Maintains a snapshot of immutable field values and compares against
    current values to detect unauthorized changes.
    """

    def __init__(self, *args, project="default", **kwargs):
        """
        Initialize ImmutableGuard.

        Parameters
        ----------
        snapshot_path : str, optional
            Path to the snapshot file for storing immutable field values.
            If None, uses default path for the project.
        project : str, optional
            Project ID for path resolution, defaults to "default"
        """
        # Handle backward compatibility for snapshot_path parameter
        snapshot_path = None
        if args:
            snapshot_path = args[0]
        elif "snapshot_path" in kwargs:
            snapshot_path = kwargs.pop("snapshot_path")

        self.project = project
        if snapshot_path is None:
            self.snapshot_path = data_path("immutable_snapshot.json", project)
        else:
            self.snapshot_path = snapshot_path

    def _load_characters(self, characters_path: str = None) -> Dict[str, Any]:
        """
        Load character data from JSON file.

        Parameters
        ----------
        characters_path : str, optional
            Path to characters.json file.
            If None, uses default path for the project.

        Returns
        -------
        Dict[str, Any]
            Character data dictionary
        """
        if characters_path is None:
            characters_path = data_path("characters.json", self.project)

        try:
            with open(characters_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
        except json.JSONDecodeError:
            return {}

    def _load_snapshot(self) -> Dict[str, Dict[str, Any]]:
        """
        Load immutable field snapshot.

        Returns
        -------
        Dict[str, Dict[str, Any]]
            Snapshot of immutable fields by character
        """
        try:
            with open(self.snapshot_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
        except json.JSONDecodeError:
            return {}

    def _save_snapshot(self, snapshot: Dict[str, Dict[str, Any]]) -> None:
        """
        Save immutable field snapshot to disk.

        Parameters
        ----------
        snapshot : Dict[str, Dict[str, Any]]
            Snapshot data to save
        """
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.snapshot_path), exist_ok=True)

        with open(self.snapshot_path, "w", encoding="utf-8") as f:
            json.dump(snapshot, f, ensure_ascii=False, indent=2)

    def _extract_immutable_fields(
        self, characters: Dict[str, Any]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Extract immutable field values from character data.

        Parameters
        ----------
        characters : Dict[str, Any]
            Full character data

        Returns
        -------
        Dict[str, Dict[str, Any]]
            Immutable fields by character
        """
        immutable_data = {}

        for char_id, char_data in characters.items():
            if not isinstance(char_data, dict):
                continue

            immutable_fields = char_data.get("immutable", [])
            if not immutable_fields:
                continue

            char_immutable = {}
            for field in immutable_fields:
                if field in char_data:
                    char_immutable[field] = char_data[field]

            if char_immutable:
                immutable_data[char_id] = char_immutable

        return immutable_data

    def check(self, current_chars: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check for immutable field violations.

        Parameters
        ----------
        current_chars : Dict[str, Any]
            Current character data to check

        Returns
        -------
        Dict[str, Any]
            Check results with flags and violations

        Raises
        ------
        RetryException
            If immutable field violations are detected
        """
        results = {
            "violations": [],
            "flags": {},
            "passed": True,
            "snapshot_created": False,
        }

        # Extract current immutable field values
        current_immutable = self._extract_immutable_fields(current_chars)

        # Load existing snapshot
        snapshot = self._load_snapshot()

        # If no snapshot exists, create one and return success
        if not snapshot:
            self._save_snapshot(current_immutable)
            results["snapshot_created"] = True
            return results

        # Compare current values with snapshot
        violations = []

        for char_id, char_immutable in current_immutable.items():
            if char_id not in snapshot:
                # New character - add to snapshot
                snapshot[char_id] = char_immutable
                continue

            snapshot_char = snapshot[char_id]

            for field, current_value in char_immutable.items():
                if field in snapshot_char:
                    snapshot_value = snapshot_char[field]
                    if current_value != snapshot_value:
                        violations.append(
                            {
                                "character": char_id,
                                "field": field,
                                "original_value": snapshot_value,
                                "current_value": current_value,
                            }
                        )
                else:
                    # New immutable field - add to snapshot
                    snapshot_char[field] = current_value

        # Save updated snapshot (for new characters/fields)
        self._save_snapshot(snapshot)

        results["violations"] = violations

        if violations:
            results["passed"] = False

            # Create flags
            flags = {
                "immutable_breach": {
                    "count": len(violations),
                    "details": violations,
                    "message": f"{len(violations)} immutable field violation(s) detected",
                }
            }
            results["flags"] = flags

            # Create error message
            violation_details = []
            for v in violations:
                violation_details.append(
                    f"{v['character']}.{v['field']}: {v['original_value']} → {v['current_value']}"
                )

            error_message = "Immutable field violations: " + "; ".join(
                violation_details
            )

            raise RetryException(
                message=error_message, flags=flags, guard_name="immutable_guard"
            )

        return results


def check_immutable_guard(
    current_chars: Dict[str, Any], project: str = "default"
) -> Dict[str, Any]:
    """
    Check immutable guard with current character data.

    Parameters
    ----------
    current_chars : Dict[str, Any]
        Current character data
    project : str, optional
        Project ID for path resolution, defaults to "default"

    Returns
    -------
    Dict[str, Any]
        Check results

    Raises
    ------
    RetryException
        If immutable violations are detected
    """
    guard = ImmutableGuard(project=project)
    return guard.check(current_chars)


def immutable_guard(current_chars: Dict[str, Any], project: str = "default") -> bool:
    """
    Main entry point for immutable guard check.

    Parameters
    ----------
    current_chars : Dict[str, Any]
        Current character data to check
    project : str, optional
        Project ID for path resolution, defaults to "default"

    Returns
    -------
    bool
        True if no violations detected

    Raises
    ------
    RetryException
        If immutable violations are detected
    """
    try:
        check_immutable_guard(current_chars, project)
        return True
    except RetryException:
        # Re-raise the exception to be handled by the caller
        raise
