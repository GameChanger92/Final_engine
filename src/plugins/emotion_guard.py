"""
emotion_guard.py

Emotion Guard for Final Engine - detects sudden emotional transitions.

Monitors emotion changes between text segments using 7-dimensional emotion vectors
and cosine distance. Raises RetryException when emotional delta > 0.7.

Emotion categories: joy, sadness, anger, fear, surprise, disgust, neutral
"""

import re

import numpy as np

from src.core.guard_registry import BaseGuard, register_guard
from src.exceptions import RetryException

# Emotion keyword mapping for simple classification
EMOTION_KEYWORDS = {
    "joy": [
        "happy",
        "joy",
        "joyful",
        "glad",
        "cheerful",
        "delighted",
        "pleased",
        "excited",
        "thrilled",
        "elated",
        "content",
        "satisfied",
        "blissful",
        "ecstatic",
        "euphoric",
        "jubilant",
        "merry",
        "upbeat",
        "positive",
        "wonderful",
        "amazing",
        "fantastic",
        "great",
        "excellent",
        "brilliant",
        "smile",
        "smiling",
        "laugh",
        "laughing",
        "celebration",
        "celebrate",
    ],
    "sadness": [
        "sad",
        "sadness",
        "sorrow",
        "grief",
        "melancholy",
        "depressed",
        "gloomy",
        "miserable",
        "dejected",
        "despondent",
        "downcast",
        "blue",
        "heartbroken",
        "mournful",
        "somber",
        "sorrowful",
        "forlorn",
        "glum",
        "crying",
        "cry",
        "tears",
        "weep",
        "weeping",
        "sob",
        "sobbing",
        "disappointed",
        "disappointed",
        "regret",
        "loss",
        "lost",
        "lonely",
    ],
    "anger": [
        "angry",
        "anger",
        "mad",
        "furious",
        "rage",
        "enraged",
        "livid",
        "irate",
        "wrathful",
        "outraged",
        "incensed",
        "indignant",
        "hostile",
        "annoyed",
        "irritated",
        "frustrated",
        "aggravated",
        "infuriated",
        "resentful",
        "bitter",
        "hatred",
        "hate",
        "loathe",
        "despise",
        "fight",
        "fighting",
        "attack",
        "violent",
        "aggressive",
        "confrontation",
    ],
    "fear": [
        "fear",
        "afraid",
        "scared",
        "frightened",
        "terrified",
        "horrified",
        "panicked",
        "anxious",
        "worried",
        "nervous",
        "apprehensive",
        "uneasy",
        "alarmed",
        "startled",
        "petrified",
        "dread",
        "dreading",
        "phobia",
        "paranoid",
        "timid",
        "cowardly",
        "trembling",
        "shaking",
        "horror",
        "terror",
        "nightmare",
        "threat",
        "threatening",
        "danger",
        "dangerous",
    ],
    "surprise": [
        "surprised",
        "surprise",
        "amazed",
        "astonished",
        "astounded",
        "stunned",
        "shocked",
        "startled",
        "bewildered",
        "perplexed",
        "confused",
        "puzzled",
        "baffled",
        "flabbergasted",
        "speechless",
        "unexpected",
        "sudden",
        "suddenly",
        "wow",
        "whoa",
        "incredible",
        "unbelievable",
        "remarkable",
        "extraordinary",
        "strange",
        "odd",
        "curious",
        "mystery",
        "mysterious",
        "wonder",
        "wondering",
    ],
    "disgust": [
        "disgusted",
        "disgust",
        "revolted",
        "repulsed",
        "nauseated",
        "sick",
        "sickening",
        "gross",
        "nasty",
        "foul",
        "vile",
        "repugnant",
        "loathsome",
        "abhorrent",
        "detestable",
        "offensive",
        "appalling",
        "horrible",
        "awful",
        "terrible",
        "dreadful",
        "hideous",
        "ugly",
        "repulsive",
        "contempt",
        "contemptuous",
        "scorn",
        "disdain",
        "revulsion",
    ],
    "neutral": [
        "normal",
        "ordinary",
        "usual",
        "typical",
        "regular",
        "standard",
        "common",
        "average",
        "routine",
        "everyday",
        "plain",
        "simple",
        "calm",
        "peaceful",
        "quiet",
        "still",
        "steady",
        "stable",
        "balanced",
        "neutral",
        "indifferent",
        "detached",
        "objective",
        "factual",
    ],
}


def classify_emotions(text: str) -> dict[str, float]:
    """
    Classify emotions in text using keyword-based approach.

    Parameters
    ----------
    text : str
        Input text to analyze

    Returns
    -------
    Dict[str, float]
        Dictionary mapping emotion names to scores (0-1)
    """
    if not text.strip():
        # Empty text is considered neutral
        return dict.fromkeys(EMOTION_KEYWORDS.keys(), 0.0)

    # Clean and tokenize text
    words = re.findall(r"\b\w+\b", text.lower())
    if not words:
        return dict.fromkeys(EMOTION_KEYWORDS.keys(), 0.0)

    # Count emotion keywords
    emotion_counts = dict.fromkeys(EMOTION_KEYWORDS.keys(), 0)
    total_words = len(words)

    for word in words:
        for emotion, keywords in EMOTION_KEYWORDS.items():
            if word in keywords:
                emotion_counts[emotion] += 1

    # Calculate raw emotion scores
    emotion_scores = {}
    for emotion, count in emotion_counts.items():
        if count > 0:
            # Score based on frequency, but cap it to prevent extremes
            score = min(count / total_words * 5, 0.8)  # Max score of 0.8
            emotion_scores[emotion] = score
        else:
            emotion_scores[emotion] = 0.0

    # Always add significant neutral component to create mixed emotional states
    # This prevents pure single-emotion vectors which cause cosine distance issues
    base_neutral = 0.3
    emotion_scores["neutral"] = max(emotion_scores["neutral"], base_neutral)

    # If no emotional content found, make it fully neutral
    if sum(emotion_scores[e] for e in emotion_scores if e != "neutral") == 0:
        emotion_scores = dict.fromkeys(EMOTION_KEYWORDS.keys(), 0.0)
        emotion_scores["neutral"] = 1.0
        return emotion_scores

    # Smooth the scores to prevent extreme values
    # Add small amounts of related emotions to create more realistic profiles
    smoothed_scores = emotion_scores.copy()

    # Add cross-emotion influences (emotional complexity)
    if emotion_scores["joy"] > 0:
        smoothed_scores["surprise"] += emotion_scores["joy"] * 0.1
    if emotion_scores["sadness"] > 0:
        smoothed_scores["fear"] += emotion_scores["sadness"] * 0.1
    if emotion_scores["anger"] > 0:
        smoothed_scores["fear"] += emotion_scores["anger"] * 0.05
        smoothed_scores["disgust"] += emotion_scores["anger"] * 0.05
    if emotion_scores["fear"] > 0:
        smoothed_scores["sadness"] += emotion_scores["fear"] * 0.1

    # Normalize to prevent values from going over 1.0
    for emotion in smoothed_scores:
        smoothed_scores[emotion] = min(smoothed_scores[emotion], 1.0)

    return smoothed_scores


def emotions_to_vector(emotion_scores: dict[str, float]) -> np.ndarray:
    """
    Convert emotion scores dictionary to numpy vector.

    Parameters
    ----------
    emotion_scores : Dict[str, float]
        Dictionary mapping emotion names to scores

    Returns
    -------
    np.ndarray
        7-dimensional emotion vector
    """
    # Ensure consistent ordering
    emotion_order = [
        "joy",
        "sadness",
        "anger",
        "fear",
        "surprise",
        "disgust",
        "neutral",
    ]
    vector = np.array([emotion_scores.get(emotion, 0.0) for emotion in emotion_order])
    return vector


def cosine_delta(v1: np.ndarray, v2: np.ndarray) -> float:
    """
    Calculate cosine delta between two vectors.

    Cosine delta = 1 - cosine_similarity

    Parameters
    ----------
    v1 : np.ndarray
        First emotion vector
    v2 : np.ndarray
        Second emotion vector

    Returns
    -------
    float
        Cosine delta value (0-2, where 0 = identical, 2 = opposite)
    """
    # Handle zero vectors to prevent division by zero
    if not np.any(v1) or not np.any(v2):
        return 0.0

    # Calculate cosine similarity
    dot_product = np.dot(v1, v2)
    norm_v1 = np.linalg.norm(v1)
    norm_v2 = np.linalg.norm(v2)

    # Prevent division by zero
    if norm_v1 == 0 or norm_v2 == 0:
        return 0.0

    cosine_similarity = dot_product / (norm_v1 * norm_v2)

    # Ensure cosine similarity is within [-1, 1] range due to floating point errors
    cosine_similarity = np.clip(cosine_similarity, -1.0, 1.0)

    # Calculate cosine delta
    cosine_delta_value = 1 - cosine_similarity

    return cosine_delta_value


def calculate_emotion_delta(prev_text: str, curr_text: str) -> float:
    """
    Calculate emotion delta between two text segments.

    Parameters
    ----------
    prev_text : str
        Previous text segment
    curr_text : str
        Current text segment

    Returns
    -------
    float
        Emotion delta value (0-2)
    """
    # Classify emotions in both texts
    prev_emotions = classify_emotions(prev_text)
    curr_emotions = classify_emotions(curr_text)

    # Convert to vectors
    prev_vector = emotions_to_vector(prev_emotions)
    curr_vector = emotions_to_vector(curr_emotions)

    # Calculate cosine delta
    delta = cosine_delta(prev_vector, curr_vector)

    # Special handling for neutral-to-emotion transitions
    # If one text is predominantly neutral and the other has strong emotions, increase sensitivity
    prev_neutral_dominant = prev_emotions["neutral"] > 0.8
    curr_neutral_dominant = curr_emotions["neutral"] > 0.8

    # Check if there's a strong emotion in one but not the other
    strong_emotions = ["joy", "sadness", "anger", "fear", "surprise", "disgust"]
    prev_max_emotion = max(prev_emotions[e] for e in strong_emotions)
    curr_max_emotion = max(curr_emotions[e] for e in strong_emotions)

    # If transitioning from neutral to strong emotion or vice versa, amplify the delta
    if (prev_neutral_dominant and curr_max_emotion > 0.6) or (
        curr_neutral_dominant and prev_max_emotion > 0.6
    ):
        # Amplify the delta for neutral-to-emotion transitions
        emotion_intensity_diff = abs(prev_max_emotion - curr_max_emotion)
        if emotion_intensity_diff > 0.5:
            delta = min(delta * 1.2, 2.0)  # Boost delta but cap at 2.0

    return delta


def check_emotion_guard(prev_text: str, curr_text: str) -> dict[str, any]:
    """
    Run emotion guard checks on text segments.

    Parameters
    ----------
    prev_text : str
        Previous text segment
    curr_text : str
        Current text segment

    Returns
    -------
    Dict[str, any]
        Results containing emotion delta and flags

    Raises
    ------
    RetryException
        If emotion delta exceeds threshold
    """
    results = {
        "emotion_delta": 0.0,
        "prev_emotions": {},
        "curr_emotions": {},
        "flags": {},
        "passed": True,
    }

    # Calculate emotion delta
    delta = calculate_emotion_delta(prev_text, curr_text)
    prev_emotions = classify_emotions(prev_text)
    curr_emotions = classify_emotions(curr_text)

    results["emotion_delta"] = delta
    results["prev_emotions"] = prev_emotions
    results["curr_emotions"] = curr_emotions

    # Check threshold
    threshold = 0.7
    flags = {}

    if delta > threshold:
        flags["emotion_jump"] = {
            "value": delta,
            "threshold": threshold,
            "message": f"Emotion delta {delta:.3f} exceeds threshold {threshold}",
        }

    results["flags"] = flags

    if flags:
        results["passed"] = False
        raise RetryException(message="Emotion jump", flags=flags, guard_name="emotion_guard")

    return results


def emotion_guard(prev_text: str, curr_text: str) -> bool:
    """
    Main entry point for emotion guard check.

    Parameters
    ----------
    prev_text : str
        Previous text segment
    curr_text : str
        Current text segment

    Returns
    -------
    bool
        True if emotion transition is acceptable

    Raises
    ------
    RetryException
        If emotion delta exceeds threshold
    """
    try:
        check_emotion_guard(prev_text, curr_text)
        return True
    except RetryException:
        # Re-raise the exception to be handled by the caller
        raise


@register_guard(order=2)
class EmotionGuard(BaseGuard):
    """
    Emotion Guard class for emotional transition validation.

    Provides class-based interface for emotion change detection between
    text segments using emotion classification and delta analysis.
    """

    def check(self, prev_text: str, curr_text: str) -> dict[str, any]:
        """
        Check for emotional transition violations.

        Parameters
        ----------
        prev_text : str
            Previous text segment
        curr_text : str
            Current text segment

        Returns
        -------
        Dict[str, any]
            Check results with emotion metrics and pass/fail status

        Raises
        ------
        RetryException
            If emotional delta exceeds threshold
        """
        return check_emotion_guard(prev_text, curr_text)
