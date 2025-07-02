from src.scene_maker import generate_scene_points, make_scenes

dummy_beat = {"idx": 1, "summary": "Test Beat", "anchor": False}


def test_len_is_10():
    assert len(make_scenes(dummy_beat)) == 10


def test_first_idx_is_1():
    assert make_scenes(dummy_beat)[0]["idx"] == 1


def test_beat_id_assignment():
    scenes = make_scenes(dummy_beat)
    assert all(scene["beat_id"] == 1 for scene in scenes)


def test_generate_scene_points():
    scenes = generate_scene_points("TEST")
    assert len(scenes) == 10
    assert scenes[0]["idx"] == 1
    assert all("TEST" in scene["desc"] for scene in scenes)


def test_scene_structure():
    scenes = make_scenes(dummy_beat)
    for scene in scenes:
        assert "idx" in scene
        assert "desc" in scene
        assert "beat_id" in scene
        assert "type" in scene
        assert scene["type"] == "placeholder"
