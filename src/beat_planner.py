"""
beat_planner.py

임시(placeholder) 버전:
에피소드 하나당 10개의 기본 비트를 반환합니다.
나중에 실제 로직으로 교체할 예정입니다.
"""

from typing import List, Dict


def plan_beats(ep_num: int, anchors: List[Dict]) -> List[Dict]:
    """
    Create 10 simple placeholder beats for a given episode number.

    Parameters
    ----------
    ep_num : int
        Episode number (1-based).
    anchors : List[Dict]
        Anchor list (현재 단계에선 사용하지 않음).

    Returns
    -------
    List[Dict]
        List of 10 beat dictionaries, each with idx & summary.
    """
    return [
        {"idx": i + 1, "summary": f"Placeholder beat {i+1} for ep {ep_num}"}
        for i in range(10)
    ]


def make_beats(arc_json: dict) -> list[dict]:
    """
    Generate 10 beat dictionaries for a given story arc.

    Parameters
    ----------
    arc_json : dict
        Example: {"title": "Prologue", "anchor_ep": 3}

    Returns
    -------
    list[dict]
        [{"idx": 1, "summary": "...", "anchor": False}, ...]
    """
    title = arc_json.get("title", "Untitled")
    anchor_ep = arc_json.get("anchor_ep")

    beats = []
    for i in range(10):
        idx = i + 1
        beats.append(
            {
                "idx": idx,
                "summary": f"{title} — beat {idx}",
                "anchor": (idx == anchor_ep),
            }
        )
    return beats
