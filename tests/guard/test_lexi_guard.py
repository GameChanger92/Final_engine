"""
test_lexi_guard.py

Tests for the Lexi Guard - 10 tests total (5 pass, 5 fail)
Tests TTR and 3-gram duplication rate functionality.
"""

import pytest

from src.exceptions import RetryException
from src.plugins.lexi_guard import (
    calculate_3gram_duplication_rate,
    calculate_ttr,
    lexi_guard,
)

# Test cases that should PASS (5 tests)


def test_lexi_guard_passes_diverse_text():
    """Test that diverse text with good TTR and low 3-gram duplication passes."""
    text = """
    The brave knight ventured through the mysterious forest, encountering 
    various magical creatures along his journey. Each step brought new 
    challenges and unexpected discoveries. Ancient trees whispered secrets 
    of forgotten civilizations, while colorful birds sang melodies that 
    seemed to guide him forward through the winding path.
    """

    # This should pass - diverse vocabulary and minimal repetition
    result = lexi_guard(text)
    assert result is True


def test_lexi_guard_passes_varied_vocabulary():
    """Test text with varied vocabulary and unique phrases passes."""
    text = """
    Scientists recently discovered fascinating phenomena in deep ocean trenches.
    Marine biologists documented unprecedented biodiversity patterns among
    previously unknown species. Their research methodology involved sophisticated
    underwater exploration techniques and advanced genetic analysis procedures.
    """

    result = lexi_guard(text)
    assert result is True


def test_lexi_guard_passes_creative_writing():
    """Test creative writing with rich language passes."""
    text = """
    Autumn leaves danced gracefully in the crisp morning breeze. Golden sunlight
    filtered through towering oak branches, casting intricate shadows across
    the meadow below. A gentle stream meandered between smooth river stones,
    creating a peaceful symphony that echoed throughout the tranquil valley.
    """

    result = lexi_guard(text)
    assert result is True


def test_lexi_guard_passes_technical_content():
    """Test technical content with specialized vocabulary passes."""
    text = """
    The algorithm implements a sophisticated machine learning approach using
    convolutional neural networks. Data preprocessing involves normalization
    techniques and feature extraction methods. Performance optimization requires
    careful hyperparameter tuning and cross-validation procedures.
    """

    result = lexi_guard(text)
    assert result is True


def test_lexi_guard_passes_narrative_text():
    """Test narrative text with good variety passes."""
    text = """
    Sarah opened the mysterious letter with trembling hands. Inside, elegant
    handwriting revealed an invitation to an exclusive gathering. The message
    contained cryptic references to ancient artifacts and hidden treasures
    waiting to be discovered by worthy adventurers.
    """

    result = lexi_guard(text)
    assert result is True


# Test cases that should FAIL (5 tests)


def test_lexi_guard_fails_repetitive_text():
    """Test that highly repetitive text fails TTR check."""
    text = """
    The cat sat on the mat. The cat sat on the mat. The cat sat on the mat.
    The cat sat on the mat. The cat sat on the mat. The cat sat on the mat.
    The cat sat on the mat. The cat sat on the mat. The cat sat on the mat.
    """

    with pytest.raises(RetryException) as exc_info:
        lexi_guard(text)

    exception = exc_info.value
    assert exception.guard_name == "lexi_guard"
    assert "too_repetitive" in exception.flags
    assert exception.flags["too_repetitive"]["value"] < 0.17


def test_lexi_guard_fails_duplicate_phrases():
    """Test that text with many duplicate 3-grams fails."""
    text = """
    I went to the store and bought some food. I went to the store and bought
    some drinks. I went to the store and bought some snacks. I went to the
    store and bought some candy. I went to the store and bought some fruit.
    """

    with pytest.raises(RetryException) as exc_info:
        lexi_guard(text)

    exception = exc_info.value
    assert exception.guard_name == "lexi_guard"
    assert "duplicate_phrases" in exception.flags
    assert exception.flags["duplicate_phrases"]["value"] > 0.06


def test_lexi_guard_fails_both_checks():
    """Test text that fails both TTR and 3-gram checks."""
    text = """
    Yes yes yes yes yes yes yes yes yes yes. Yes yes yes yes yes yes yes.
    Yes yes yes yes yes yes yes yes. Yes yes yes indeed yes yes yes.
    """

    with pytest.raises(RetryException) as exc_info:
        lexi_guard(text)

    exception = exc_info.value
    assert exception.guard_name == "lexi_guard"
    assert "too_repetitive" in exception.flags
    assert "duplicate_phrases" in exception.flags


def test_lexi_guard_fails_low_vocabulary_diversity():
    """Test text with very limited vocabulary fails."""
    text = """
    Good good good very good. Very good good good. Good very very good.
    Very good good very good. Good good very good good. Very very good good.
    Good very good good very. Very good very good good good.
    """

    with pytest.raises(RetryException) as exc_info:
        lexi_guard(text)

    exception = exc_info.value
    assert exception.guard_name == "lexi_guard"
    assert "too_repetitive" in exception.flags


def test_lexi_guard_fails_phrase_repetition():
    """Test text with repeated phrases fails 3-gram check."""
    text = """
    The quick brown fox jumps over the lazy dog today. The quick brown
    fox jumps over another lazy dog yesterday. The quick brown fox
    jumps over the sleeping dog tomorrow. The quick brown fox jumps
    over the tired dog again.
    """

    with pytest.raises(RetryException) as exc_info:
        lexi_guard(text)

    exception = exc_info.value
    assert exception.guard_name == "lexi_guard"
    assert "duplicate_phrases" in exception.flags


# Additional unit tests for individual functions


def test_calculate_ttr_empty_text():
    """Test TTR calculation with empty text."""
    assert calculate_ttr("") == 1.0
    assert calculate_ttr("   ") == 1.0


def test_calculate_ttr_single_word():
    """Test TTR calculation with single word."""
    assert calculate_ttr("hello") == 1.0


def test_calculate_ttr_all_different_words():
    """Test TTR calculation with all different words."""
    ttr = calculate_ttr("hello world python programming")
    assert ttr == 1.0


def test_calculate_ttr_repeated_words():
    """Test TTR calculation with repeated words."""
    ttr = calculate_ttr("hello hello world world")
    assert ttr == 0.5  # 2 unique words out of 4 total


def test_calculate_3gram_duplication_rate_short_text():
    """Test 3-gram calculation with text shorter than 3 words."""
    assert calculate_3gram_duplication_rate("") == 0.0
    assert calculate_3gram_duplication_rate("one") == 0.0
    assert calculate_3gram_duplication_rate("one two") == 0.0


def test_calculate_3gram_duplication_rate_no_duplicates():
    """Test 3-gram calculation with no duplicates."""
    rate = calculate_3gram_duplication_rate("the quick brown fox jumps")
    assert rate == 0.0  # 3 unique 3-grams, no duplicates


def test_calculate_3gram_duplication_rate_with_duplicates():
    """Test 3-gram calculation with duplicates."""
    # "the cat sat" appears twice
    rate = calculate_3gram_duplication_rate("the cat sat on the cat sat")
    assert rate > 0.0  # Should have some duplication
