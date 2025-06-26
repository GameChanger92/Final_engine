from src.beat_planner import plan_beats


def test_len_is_10():
    beats = plan_beats(1, [])
    assert len(beats) == 10
