"""
test_emotion_guard.py

Tests for the Emotion Guard - comprehensive test suite
Tests emotion classification and delta calculation functionality.
"""

import numpy as np
import pytest

from src.exceptions import RetryException
from src.plugins.emotion_guard import (
    calculate_emotion_delta,
    check_emotion_guard,
    classify_emotions,
    cosine_delta,
    emotion_guard,
    emotions_to_vector,
)

# Test cases that should PASS (normal emotion transitions)


def test_emotion_guard_passes_similar_emotions():
    """Test that similar emotional content passes."""
    prev_text = "I was really happy and excited about the news today."
    curr_text = "The wonderful announcement made me feel joyful and pleased."

    result = emotion_guard(prev_text, curr_text)
    assert result is True


def test_emotion_guard_passes_neutral_transition():
    """Test that neutral emotional transitions pass."""
    prev_text = "The weather report shows it will be partly cloudy tomorrow."
    curr_text = "According to the schedule, the meeting is at three o'clock."

    result = emotion_guard(prev_text, curr_text)
    assert result is True


def test_emotion_guard_passes_gradual_change():
    """Test that gradual emotional changes pass."""
    prev_text = "The project is going well and I'm pleased with the progress."
    curr_text = "I have some concerns about the timeline but we're making progress."

    result = emotion_guard(prev_text, curr_text)
    assert result is True


def test_emotion_guard_passes_mild_sadness_to_neutral():
    """Test transition from mild sadness to neutral passes."""
    prev_text = "I was a little disappointed with the results."
    curr_text = "The next step is to review the data and make adjustments."

    result = emotion_guard(prev_text, curr_text)
    assert result is True


def test_emotion_guard_passes_consistent_tone():
    """Test that consistent emotional tone passes."""
    prev_text = "The project documentation needs to be updated regularly."
    curr_text = "Standard procedures require thorough testing before deployment."

    result = emotion_guard(prev_text, curr_text)
    assert result is True


# Test cases that should FAIL (sudden emotion changes)


def test_emotion_guard_fails_joy_to_anger():
    """Test that sudden change from joy to anger fails."""
    prev_text = """
    I was absolutely thrilled and ecstatic about winning the award! 
    The joy and happiness filled my heart completely. What a wonderful, 
    amazing, fantastic day this has been! I'm so delighted and pleased 
    with this incredible achievement.
    """
    curr_text = """
    I am absolutely furious and enraged about this situation! 
    The anger and hatred consume me completely. What a terrible, 
    awful, horrible mess this has become! I'm so mad and livid 
    about this outrageous betrayal.
    """

    with pytest.raises(RetryException) as exc_info:
        emotion_guard(prev_text, curr_text)

    exception = exc_info.value
    assert exception.guard_name == "emotion_guard"
    assert "emotion_jump" in exception.flags
    assert exception.flags["emotion_jump"]["value"] > 0.7


def test_emotion_guard_fails_neutral_to_terror():
    """Test that sudden change from neutral to extreme fear fails."""
    prev_text = """
    The meeting agenda includes reviewing quarterly reports 
    and discussing standard operational procedures. Regular 
    updates will be provided as usual.
    """
    curr_text = """
    I am absolutely terrified and horrified by the nightmare! 
    The fear and panic overwhelm me completely. This dreadful, 
    frightening situation fills me with terror and horror. 
    I'm so scared and afraid of the dangerous threat.
    """

    with pytest.raises(RetryException) as exc_info:
        emotion_guard(prev_text, curr_text)

    exception = exc_info.value
    assert exception.guard_name == "emotion_guard"
    assert "emotion_jump" in exception.flags
    assert exception.flags["emotion_jump"]["value"] > 0.7


def test_emotion_guard_fails_sadness_to_extreme_joy():
    """Test that sudden change from sadness to extreme joy fails."""
    prev_text = """
    I feel so heartbroken and miserable about the loss. 
    The sadness and grief overwhelm me. Tears of sorrow 
    flow as I mourn this devastating situation.
    """
    curr_text = """
    I am absolutely ecstatic and euphoric about this fantastic news! 
    The joy and happiness explode within me! This is the most 
    wonderful, amazing, brilliant thing that could happen!
    """

    with pytest.raises(RetryException) as exc_info:
        emotion_guard(prev_text, curr_text)

    exception = exc_info.value
    assert exception.guard_name == "emotion_guard"
    assert "emotion_jump" in exception.flags
    assert exception.flags["emotion_jump"]["value"] > 0.7


def test_emotion_guard_fails_disgust_to_surprise():
    """Test that sudden change from disgust to surprise fails."""
    prev_text = """
    This is absolutely disgusting and revolting! I'm nauseated 
    and repulsed by this vile, foul, gross situation. The 
    horrible, awful smell makes me sick to my stomach.
    """
    curr_text = """
    I am completely astonished and amazed by this incredible 
    discovery! How surprising and unexpected this remarkable 
    finding is! What a mysterious and wonderful revelation!
    """

    with pytest.raises(RetryException) as exc_info:
        emotion_guard(prev_text, curr_text)

    exception = exc_info.value
    assert exception.guard_name == "emotion_guard"
    assert "emotion_jump" in exception.flags
    assert exception.flags["emotion_jump"]["value"] > 0.7


def test_emotion_guard_fails_fear_to_anger():
    """Test that sudden change from fear to anger fails."""
    prev_text = """
    I'm absolutely terrified and frightened by the approaching storm. 
    The fear and anxiety make me tremble with worry. This dangerous 
    situation fills me with dread and panic.
    """
    curr_text = """
    I am furious and enraged about this incompetent response! 
    The anger and rage consume me completely. This is absolutely 
    outrageous and infuriating! I hate this situation!
    """

    with pytest.raises(RetryException) as exc_info:
        emotion_guard(prev_text, curr_text)

    exception = exc_info.value
    assert exception.guard_name == "emotion_guard"
    assert "emotion_jump" in exception.flags
    assert exception.flags["emotion_jump"]["value"] > 0.7


# Unit tests for helper functions


def test_classify_emotions_empty_text():
    """Test emotion classification with empty text."""
    emotions = classify_emotions("")
    assert emotions["neutral"] == 0.0
    assert all(score == 0.0 for score in emotions.values())


def test_classify_emotions_neutral_text():
    """Test emotion classification with neutral text."""
    text = "The standard procedure requires documentation and regular updates."
    emotions = classify_emotions(text)
    assert emotions["neutral"] > 0.0
    # Other emotions should be lower or zero
    assert emotions["joy"] <= emotions["neutral"]


def test_classify_emotions_joy_text():
    """Test emotion classification with joyful text."""
    text = "I'm so happy and excited about this wonderful amazing news!"
    emotions = classify_emotions(text)
    assert emotions["joy"] > 0.0
    assert emotions["joy"] >= emotions["sadness"]


def test_classify_emotions_anger_text():
    """Test emotion classification with angry text."""
    text = "I'm absolutely furious and mad about this outrageous situation!"
    emotions = classify_emotions(text)
    assert emotions["anger"] > 0.0
    assert emotions["anger"] >= emotions["joy"]


def test_emotions_to_vector():
    """Test conversion of emotion scores to vector."""
    emotions = {
        "joy": 0.5,
        "sadness": 0.2,
        "anger": 0.0,
        "fear": 0.1,
        "surprise": 0.3,
        "disgust": 0.0,
        "neutral": 0.4,
    }
    vector = emotions_to_vector(emotions)

    assert len(vector) == 7
    assert vector[0] == 0.5  # joy
    assert vector[1] == 0.2  # sadness
    assert vector[2] == 0.0  # anger
    assert vector[3] == 0.1  # fear
    assert vector[4] == 0.3  # surprise
    assert vector[5] == 0.0  # disgust
    assert vector[6] == 0.4  # neutral


def test_cosine_delta_identical_vectors():
    """Test cosine delta with identical vectors."""
    v1 = np.array([1.0, 0.5, 0.2, 0.0, 0.3, 0.1, 0.4])
    v2 = np.array([1.0, 0.5, 0.2, 0.0, 0.3, 0.1, 0.4])

    delta = cosine_delta(v1, v2)
    assert abs(delta - 0.0) < 1e-10  # Should be very close to 0


def test_cosine_delta_zero_vectors():
    """Test cosine delta with zero vectors."""
    v1 = np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
    v2 = np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])

    delta = cosine_delta(v1, v2)
    assert delta == 0.0


def test_cosine_delta_one_zero_vector():
    """Test cosine delta with one zero vector."""
    v1 = np.array([1.0, 0.5, 0.2, 0.0, 0.3, 0.1, 0.4])
    v2 = np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])

    delta = cosine_delta(v1, v2)
    assert delta == 0.0


def test_cosine_delta_opposite_vectors():
    """Test cosine delta with opposite vectors."""
    # Create vectors that should have high cosine distance
    v1 = np.array([1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])  # Pure joy
    v2 = np.array([0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0])  # Pure sadness

    delta = cosine_delta(v1, v2)
    assert delta > 0.5  # Should be relatively high


def test_calculate_emotion_delta_similar_texts():
    """Test emotion delta calculation with similar texts."""
    prev_text = "I'm happy and excited about this."
    curr_text = "This makes me feel joyful and pleased."

    delta = calculate_emotion_delta(prev_text, curr_text)
    assert delta < 0.7  # Should be below threshold


def test_calculate_emotion_delta_different_emotions():
    """Test emotion delta calculation with very different emotions."""
    prev_text = "I'm absolutely thrilled and ecstatic about this wonderful news!"
    curr_text = "I'm completely terrified and horrified by this nightmare!"

    delta = calculate_emotion_delta(prev_text, curr_text)
    assert delta > 0.7  # Should exceed threshold


def test_check_emotion_guard_results_structure():
    """Test that check_emotion_guard returns proper structure."""
    prev_text = "The meeting went well and covered all the topics."
    curr_text = "The next steps are clear and we have a good plan."

    results = check_emotion_guard(prev_text, curr_text)

    assert "emotion_delta" in results
    assert "prev_emotions" in results
    assert "curr_emotions" in results
    assert "flags" in results
    assert "passed" in results
    assert results["passed"] is True
    assert isinstance(results["emotion_delta"], float)
    assert isinstance(results["prev_emotions"], dict)
    assert isinstance(results["curr_emotions"], dict)


def test_emotion_guard_exception_message():
    """Test that RetryException has correct message."""
    prev_text = "I'm absolutely delighted and thrilled!"
    curr_text = "I'm completely furious and enraged!"

    with pytest.raises(RetryException) as exc_info:
        emotion_guard(prev_text, curr_text)

    exception = exc_info.value
    assert str(exception).startswith("[emotion_guard] Emotion jump")
