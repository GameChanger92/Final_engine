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
from .utils.path_helper import data_path, out_path, ensure_project_dirs


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


def run_pipeline(episode_num: int, project: str = "default") -> str:
    """
    Run the complete integration pipeline.

    Parameters
    ----------
    episode_num : int
        Episode number to generate
    project : str, optional
        Project ID for path resolution, defaults to "default"

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

    # Step 6: Guard Chain - Quality checks

    # Immutable Guard - check character consistency
    try:
        from src.plugins.immutable_guard import immutable_guard

        # Load current character data for checking
        import json

        try:
            characters_path = data_path("characters.json", project)
            with open(characters_path, "r", encoding="utf-8") as f:
                characters = json.load(f)
            immutable_guard(characters, project)
            print("✅ Immutable Guard: PASSED")
        except FileNotFoundError:
            print("⚠️  Immutable Guard: No characters.json found, skipping")
    except RetryException as e:
        print(f"⚠️  Immutable Guard Warning: {e}")

    # Date Guard - check chronological progression
    try:
        from src.plugins.date_guard import date_guard

        # Create context with date for checking (if available)
        date_context = {"date": f"2024-{episode_num:02d}-01"}  # Simple date progression
        date_guard(date_context, episode_num, project)
        print("✅ Date Guard: PASSED")
    except RetryException as e:
        print(f"⚠️  Date Guard Warning: {e}")

    # Lexi Guard - check lexical quality (message only on failure)
    try:
        from src.plugins.lexi_guard import lexi_guard

        lexi_guard(draft)
        print("✅ Lexi Guard: PASSED")
    except RetryException as e:
        # In this implementation, we just show a message but don't retry
        # This follows the requirement: "실패 시 메시지만"
        print(f"⚠️  Lexi Guard Warning: {e}")

    # Rule Guard - check forbidden patterns and world rules
    try:
        from src.plugins.rule_guard import rule_guard

        rule_guard(draft, project=project)
        print("✅ Rule Guard: PASSED")
    except RetryException as e:
        # Show warning for rule violations but don't stop pipeline
        print(f"⚠️  Rule Guard Warning: {e}")

    return draft


# CLI setup
app = typer.Typer(help="Final Engine - Integration Pipeline", no_args_is_help=True)


@app.command()
def run(
    episode: int = typer.Option(1, "--episode", help="Episode number to generate"),
    project_id: str = typer.Option("default", "--project-id", help="Project ID for the story")
):
    """
    Run the complete pipeline to generate an episode.
    """
    typer.echo(f"🚀 Starting pipeline for Episode {episode} (Project: {project_id})...")

    # Ensure project directories exist
    ensure_project_dirs(project_id)

    # Run the pipeline
    typer.echo("📝 Running Arc Outliner...")
    typer.echo("⚡ Running Beat Planner...")
    typer.echo("🎬 Running Scene Maker...")
    typer.echo("🔗 Running Context Builder...")
    typer.echo("✍️  Running Draft Generator...")
    typer.echo("🛡️  Running Guard Chain...")
    typer.echo("   - Immutable Guard")
    typer.echo("   - Date Guard")
    typer.echo("   - Lexi Guard")
    typer.echo("   - Rule Guard")

    draft = run_pipeline(episode, project_id)

    # Create output directory if it doesn't exist and save to file
    output_file = out_path(f"episode_{episode}.txt", project_id)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(draft, encoding="utf-8")

    typer.echo(f"✅ Pipeline complete! Output saved to: {output_file}")
    typer.echo(f"📄 Generated {len(draft)} characters")


@app.command()
def info():
    """
    Display information about the pipeline.
    """
    typer.echo("Final Engine Integration Pipeline v1.0")
    typer.echo("Day 13 - Rule Guard Implementation")
    typer.echo("")
    typer.echo("Pipeline stages:")
    typer.echo("1. Arc Outliner → Basic arc structure")
    typer.echo("2. Beat Planner → 3 beats")
    typer.echo("3. Scene Maker → ~10 scenes total")
    typer.echo("4. Context Builder → Combined context")
    typer.echo("5. Draft Generator → Final PLACEHOLDER text")
    typer.echo("6. Guard Chain → Quality checks")
    typer.echo("   - Immutable Guard → Character consistency")
    typer.echo("   - Date Guard → Chronological progression")
    typer.echo("   - Lexi Guard → Lexical quality")
    typer.echo("   - Rule Guard → Forbidden pattern detection")


if __name__ == "__main__":
    app()
