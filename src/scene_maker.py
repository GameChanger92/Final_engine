"""
scene_maker.py

임시(placeholder) 버전:
비트 하나당 10개의 기본 씬 포인트를 반환합니다.
나중에 실제 로직으로 교체할 예정입니다.
"""

from typing import List, Dict
import typer

def make_scenes(beat_json: dict) -> list[dict]:
    """
    Generate 10 scene point dictionaries for a given beat.

    Parameters
    ----------
    beat_json : dict
        Example: {"idx": 1, "summary": "Opening beat", "anchor": False}

    Returns
    -------
    list[dict]
        [{"idx": 1, "desc": "...", "beat_id": ...}, ...]
    """
    beat_idx = beat_json.get("idx", 1)
    beat_summary = beat_json.get("summary", "Unknown beat")
    
    scenes = []
    for i in range(10):
        scene_idx = i + 1
        scenes.append({
            "idx": scene_idx,
            "desc": f"Scene {scene_idx} for {beat_summary}",
            "beat_id": beat_idx,
            "type": "placeholder"
        })
    return scenes

def generate_scene_points(beat_id: str) -> List[Dict]:
    """
    Generate scene points for a specific beat ID.
    
    Parameters
    ----------
    beat_id : str
        The beat identifier (e.g., "TEST", "beat_1", etc.)
        
    Returns
    -------
    List[Dict]
        List of 10 scene point dictionaries
    """
    # Create a mock beat for the given beat_id
    mock_beat = {
        "idx": 1,
        "summary": f"Beat {beat_id}",
        "anchor": False
    }
    
    return make_scenes(mock_beat)

# CLI setup
app = typer.Typer(help="Scene Maker - Generate scene points for beats", no_args_is_help=True)

@app.command()
def run(beat_id: str = typer.Option("TEST", "--beat-id", help="Beat ID to generate scenes for")):
    """
    Generate and display scene points for a given beat ID.
    """
    typer.echo(f"Generating scenes for beat: {beat_id}")
    
    scene_points = generate_scene_points(beat_id)
    
    typer.echo(f"Generated {len(scene_points)} scene points:")
    for scene in scene_points:
        typer.echo(f"  Scene {scene['idx']}: {scene['desc']}")
    
    typer.echo("Scene generation completed successfully.")

@app.command()
def info():
    """
    Display information about the scene maker.
    """
    typer.echo("Scene Maker v1.0 - Stub Implementation")
    typer.echo("Generates 10 placeholder scene points per beat")

if __name__ == "__main__":
    app()