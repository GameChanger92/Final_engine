"""
rule_guard.py

Rule Guard for Final Engine - checks text against forbidden patterns.

Monitors rules.json for pattern violations using regex search.
Raises RetryException on first violation found.
"""

import json
import re
from pathlib import Path
from typing import Any

from src.core.guard_registry import BaseGuard, register_guard
from src.exceptions import RetryException
from src.utils.path_helper import data_path


@register_guard(order=7)
class RuleGuard(BaseGuard):
    """
    Rule Guard - validates text against forbidden patterns from rules.json.

    Checks text against regular expression patterns defined in rules.json
    and raises RetryException if any violations are found.
    """

    def __init__(self, rule_path: str = None, project: str = "default"):
        """
        Initialize RuleGuard with rules file path.

        Parameters
        ----------
        rule_path : str, optional
            Path to rules.json file containing patterns and messages.
            If None, uses default path for the project.
        project : str, optional
            Project ID for path resolution, defaults to "default"
        """
        if rule_path is None:
            self.rule_path = data_path("rules.json", project)
        else:
            self.rule_path = Path(rule_path)
        self.rules = self._load_rules()

    def _load_rules(self) -> list[dict[str, str]]:
        """
        Load rules from JSON file.

        Returns
        -------
        List[Dict[str, str]]
            List of rule dictionaries with id, pattern, message fields

        Raises
        ------
        FileNotFoundError
            If rules file doesn't exist
        json.JSONDecodeError
            If rules file is invalid JSON
        """
        if not self.rule_path.exists():
            # Return empty rules if file doesn't exist (graceful handling)
            return []

        try:
            with open(self.rule_path, encoding="utf-8") as f:
                rules = json.load(f)

            # Validate rules structure
            if not isinstance(rules, list):
                return []

            # Filter valid rules that have required fields
            valid_rules = []
            for rule in rules:
                if (
                    isinstance(rule, dict)
                    and "id" in rule
                    and "pattern" in rule
                    and "message" in rule
                ):
                    valid_rules.append(rule)

            return valid_rules

        except (json.JSONDecodeError, OSError):
            # Return empty rules on file errors (graceful handling)
            return []

    def check(self, text: str) -> dict[str, Any]:
        """
        Check text against all rules and raise exception on first violation.

        Parameters
        ----------
        text : str
            Text to check for rule violations

        Returns
        -------
        Dict[str, Any]
            Results dictionary with passed status and violation details

        Raises
        ------
        RetryException
            If any rule violation is found (first violation reported)
        """
        results = {
            "passed": True,
            "rules_checked": len(self.rules),
            "violations": [],
            "flags": {},
        }

        if not text.strip():
            # Empty text passes all checks
            return results

        # Check each rule in order, stop at first violation
        for rule in self.rules:
            rule_id = rule["id"]
            pattern = rule["pattern"]
            message = rule["message"]

            try:
                # Use re.search to find pattern match
                match = re.search(pattern, text, re.IGNORECASE)

                if match:
                    # Rule violation found
                    violation_details = {
                        "rule_id": rule_id,
                        "pattern": pattern,
                        "message": message,
                        "matched_text": match.group(),
                        "match_position": match.start(),
                    }

                    results["passed"] = False
                    results["violations"].append(violation_details)

                    # Create flags for RetryException
                    flags = {
                        "rule_violation": {
                            "rule_id": rule_id,
                            "pattern": pattern,
                            "matched_text": match.group(),
                            "message": message,
                        }
                    }
                    results["flags"] = flags

                    # Raise exception on first violation (as per spec)
                    raise RetryException(message=message, flags=flags, guard_name="rule_guard")

            except re.error:
                # Invalid regex pattern - skip this rule
                continue

        return results


def check_rule_guard(text: str, rule_path: str = None, project: str = "default") -> dict[str, Any]:
    """
    Convenience function to run rule guard check.

    Parameters
    ----------
    text : str
        Text to analyze
    rule_path : str, optional
        Path to rules.json file.
        If None, uses default path for the project.
    project : str, optional
        Project ID for path resolution, defaults to "default"

    Returns
    -------
    Dict[str, Any]
        Results containing rule check details

    Raises
    ------
    RetryException
        If text violates any rules
    """
    guard = RuleGuard(rule_path=rule_path, project=project)
    return guard.check(text)


def rule_guard(text: str, rule_path: str = None, project: str = "default") -> bool:
    """
    Main entry point for rule guard check.

    Parameters
    ----------
    text : str
        Text to check
    rule_path : str, optional
        Path to rules.json file.
        If None, uses default path for the project.
    project : str, optional
        Project ID for path resolution, defaults to "default"

    Returns
    -------
    bool
        True if text passes all rule checks

    Raises
    ------
    RetryException
        If text violates any rules
    """
    try:
        check_rule_guard(text, rule_path, project)
        return True
    except RetryException:
        # Re-raise the exception to be handled by the caller
        raise
