"""
lexi_guard.py

Lexical Guard for Final Engine - checks text quality metrics.

Monitors:
- TTR (Type-Token Ratio) < 0.17 → "too_repetitive" flag
- 3-gram duplication rate > 0.06 → "duplicate_phrases" flag

Uses collections.Counter for efficient counting instead of textstat.
"""

import re
from typing import Dict
from src.exceptions import RetryException


def calculate_ttr(text: str) -> float:
    """
    Calculate Type-Token Ratio (TTR) for the given text.

    TTR = unique_words / total_words

    Parameters
    ----------
    text : str
        Input text to analyze

    Returns
    -------
    float
        TTR value between 0 and 1
    """
    if not text.strip():
        return 1.0  # Empty text has perfect diversity

    # Clean and tokenize text - split on whitespace and punctuation
    words = re.findall(r"\b\w+\b", text.lower())

    if not words:
        return 1.0

    total_words = len(words)
    unique_words = len(set(words))

    return unique_words / total_words


def calculate_3gram_duplication_rate(text: str) -> float:
    """
    Calculate 3-gram duplication rate for the given text.

    Duplication rate = (total_3grams - unique_3grams) / total_3grams

    Parameters
    ----------
    text : str
        Input text to analyze

    Returns
    -------
    float
        3-gram duplication rate between 0 and 1
    """
    if not text.strip():
        return 0.0  # Empty text has no duplicates

    # Clean and tokenize text
    words = re.findall(r"\b\w+\b", text.lower())

    if len(words) < 3:
        return 0.0  # Need at least 3 words for 3-grams

    # Generate 3-grams
    trigrams = []
    for i in range(len(words) - 2):
        trigram = tuple(words[i : i + 3])
        trigrams.append(trigram)

    if not trigrams:
        return 0.0

    total_3grams = len(trigrams)
    unique_3grams = len(set(trigrams))

    # Duplication rate = proportion of duplicate 3-grams
    duplication_rate = (total_3grams - unique_3grams) / total_3grams

    return duplication_rate


def check_lexi_guard(text: str) -> Dict[str, any]:
    """
    Run lexical quality checks on the given text.

    Parameters
    ----------
    text : str
        Text to analyze

    Returns
    -------
    Dict[str, any]
        Results containing TTR, 3-gram duplication rate, and flags

    Raises
    ------
    RetryException
        If text fails lexical quality checks
    """
    results = {"ttr": 0.0, "trigram_dup_rate": 0.0, "flags": {}, "passed": True}

    # Calculate metrics
    ttr = calculate_ttr(text)
    trigram_dup_rate = calculate_3gram_duplication_rate(text)

    results["ttr"] = ttr
    results["trigram_dup_rate"] = trigram_dup_rate

    # Check thresholds and set flags
    flags = {}

    if ttr < 0.17:
        flags["too_repetitive"] = {
            "value": ttr,
            "threshold": 0.17,
            "message": f"TTR {ttr:.3f} below threshold 0.17",
        }

    if trigram_dup_rate > 0.06:
        flags["duplicate_phrases"] = {
            "value": trigram_dup_rate,
            "threshold": 0.06,
            "message": f"3-gram duplication rate {trigram_dup_rate:.3f} above threshold 0.06",
        }

    results["flags"] = flags

    if flags:
        results["passed"] = False
        # Create error message
        flag_messages = [flag_data["message"] for flag_data in flags.values()]
        error_message = "Lexical quality issues detected: " + "; ".join(flag_messages)

        raise RetryException(
            message=error_message, flags=flags, guard_name="lexi_guard"
        )

    return results


def lexi_guard(text: str) -> bool:
    """
    Main entry point for lexical guard check.

    Parameters
    ----------
    text : str
        Text to check

    Returns
    -------
    bool
        True if text passes all checks

    Raises
    ------
    RetryException
        If text fails lexical quality checks
    """
    try:
        check_lexi_guard(text)
        return True
    except RetryException:
        # Re-raise the exception to be handled by the caller
        raise
