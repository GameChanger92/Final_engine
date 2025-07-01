from src.beat_planner import plan_beats


def test_beat_structure_v2():
    """Test that plan_beats returns the new v2 structure with ep_X -> seq_Y -> beat_Z format."""
    beats = plan_beats(1, [])

    # Should have episode structure
    assert "ep_1" in beats
    episode_data = beats["ep_1"]

    # Should have 6 sequences (24 total beats = 6 sequences * 4 beats)
    assert len(episode_data) == 6

    # Check that each sequence has 4 beats
    total_beats = 0
    for seq_key in episode_data:
        assert seq_key.startswith("seq_")
        seq_beats = episode_data[seq_key]
        assert len(seq_beats) == 4
        total_beats += len(seq_beats)

    # Total should be 24 beats (6 sequences * 4 beats each)
    assert total_beats == 24
