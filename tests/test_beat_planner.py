from src.beat_planner import make_beats

dummy = {"title": "Prologue", "anchor_ep": 3}


def test_len_is_10():
    assert len(make_beats(dummy)) == 10


def test_first_idx_is_1():
    assert make_beats(dummy)[0]["idx"] == 1


def test_anchor_flag():
    beats = make_beats(dummy)
    assert beats[2]["anchor"] is True
    assert all(b["anchor"] is False for b in beats if b["idx"] != 3)
