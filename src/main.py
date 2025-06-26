"""
main.py

Day 07 Integration Pipeline
Connects Arc Outliner → Beat Planner → Scene Maker → Context Builder → Draft Generator
"""

import typer
from pathlib import Path
from typing import Dict

from .beat_planner import plan_beats
from .scene_maker import make_scenes
from .context_builder import make_context
from .draft_generator import generate_draft
from .exceptions import RetryException


def create_arc_outline(episode_num: int) -> Dict:
    """
    Simple Arc Outliner - creates a basic arc structure for the episode.

    Parameters
    ----------
    episode_num : int
        Episode number

    Returns
    -------
    Dict
        Arc information with title and episode number
    """
    return {
        "title": f"Episode {episode_num} Arc",
        "episode": episode_num,
        "anchor_ep": None,
    }


def run_pipeline(episode_num: int) -> str:
    """
    Run the complete integration pipeline.

    Parameters
    ----------
    episode_num : int
        Episode number to generate

    Returns
    -------
    str
        Final draft content
    """
    # Step 1: Arc Outliner - create basic arc info
    create_arc_outline(episode_num)

    # Step 2: Beat Planner - generate beats (take first 3 for simplified version)
    all_beats = plan_beats(episode_num, [])  # Empty anchors for now
    beats = all_beats[:3]  # Take first 3 beats

    # Step 3: Scene Maker - generate scenes for each beat (aim for ~10 total scenes)
    all_scenes = []
    scenes_per_beat = [4, 3, 3]  # 4 + 3 + 3 = 10 scenes total

    for i, beat in enumerate(beats):
        beat_scenes = make_scenes(beat)
        # Take the specified number of scenes for this beat
        selected_scenes = beat_scenes[: scenes_per_beat[i]]
        all_scenes.extend(selected_scenes)

    # Step 4: Context Builder - convert scene dicts to strings and build context
    scene_descriptions = [scene["desc"] for scene in all_scenes]
    context = make_context(scene_descriptions)

    # Step 5: Draft Generator - generate final draft
    draft = generate_draft(context, episode_num)

    # Step 6: Lexi Guard - check lexical quality (message only on failure)
    try:
        from plugins.lexi_guard import lexi_guard

        lexi_guard(draft)
    except RetryException as e:
        # In this implementation, we just show a message but don't retry
        # This follows the requirement: "실패 시 메시지만"
        print(f"⚠️  Lexi Guard Warning: {e}")

    return draft


# CLI setup
app = typer.Typer(help="Final Engine - Integration Pipeline", no_args_is_help=True)


@app.command()
def run(episode: int = typer.Option(1, "--episode", help="Episode number to generate")):
    """
    Run the complete pipeline to generate an episode.
    """
    typer.echo(f"🚀 Starting pipeline for Episode {episode}...")

    # Run the pipeline
    typer.echo("📝 Running Arc Outliner...")
    typer.echo("⚡ Running Beat Planner...")
    typer.echo("🎬 Running Scene Maker...")
    typer.echo("🔗 Running Context Builder...")
    typer.echo("✍️  Running Draft Generator...")
    typer.echo("🛡️  Running Lexi Guard...")

    draft = run_pipeline(episode)

    # Create output directory if it doesn't exist
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    # Save to file
    output_file = output_dir / f"episode_{episode}.txt"
    output_file.write_text(draft, encoding="utf-8")

    typer.echo(f"✅ Pipeline complete! Output saved to: {output_file}")
    typer.echo(f"📄 Generated {len(draft)} characters")


@app.command()
def info():
    """
    Display information about the pipeline.
    """
    typer.echo("Final Engine Integration Pipeline v1.0")
    typer.echo("Day 07 - First Integration Run")
    typer.echo("")
    typer.echo("Pipeline stages:")
    typer.echo("1. Arc Outliner → Basic arc structure")
    typer.echo("2. Beat Planner → 3 beats")
    typer.echo("3. Scene Maker → ~10 scenes total")
    typer.echo("4. Context Builder → Combined context")
    typer.echo("5. Draft Generator → Final PLACEHOLDER text")
    typer.echo("6. Lexi Guard → Lexical quality check")


if __name__ == "__main__":
    app()
