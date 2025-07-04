"""
main.py

Day 07 Integration Pipeline
Connects Arc Outliner → Beat Planner → Scene Maker → Context Builder → Draft Generator
"""

import typer

from .beat_planner import plan_beats
from .context_builder import make_context
from .core.guard_registry import get_sorted_guards
from .exceptions import RetryException
from .scene_maker import make_scenes
from .utils.path_helper import data_path, ensure_project_dirs, out_path


def create_arc_outline(episode_num: int) -> dict:
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


def run_guards_auto_registry(draft: str, episode_num: int, project: str = "default") -> None:
    """
    Run all guards using auto-registry system.

    Parameters
    ----------
    draft : str
        Draft content to validate
    episode_num : int
        Episode number
    project : str, optional
        Project ID for path resolution, defaults to "default"
    """
    # Import all guards to trigger registration
    import src.plugins.anchor_guard  # noqa: F401
    import src.plugins.critique_guard  # noqa: F401
    import src.plugins.date_guard  # noqa: F401
    import src.plugins.emotion_guard  # noqa: F401
    import src.plugins.immutable_guard  # noqa: F401
    import src.plugins.lexi_guard  # noqa: F401
    import src.plugins.pacing_guard  # noqa: F401
    import src.plugins.relation_guard  # noqa: F401
    import src.plugins.rule_guard  # noqa: F401
    import src.plugins.schedule_guard  # noqa: F401

    # Get registered guards in order
    guard_classes = get_sorted_guards()

    for guard_class in guard_classes:
        guard_name = guard_class.__name__
        try:
            # Create guard instance
            guard = guard_class(project=project)

            # Prepare appropriate arguments based on guard type
            if guard_name == "LexiGuard":
                guard.check(draft)
            elif guard_name == "EmotionGuard":
                # Simple implementation - compare with neutral text
                prev_text = "This is neutral content from previous episode."
                guard.check(prev_text, draft)
            elif guard_name == "ScheduleGuard":
                guard.check(episode_num)
            elif guard_name == "ImmutableGuard":
                # Load character data if available
                import json

                try:
                    characters_path = data_path("characters.json", project)
                    with open(characters_path, encoding="utf-8") as f:
                        characters = json.load(f)
                    guard.check(characters)
                except FileNotFoundError:
                    print(f"⚠️  {guard_name}: No characters.json found, skipping")
                    continue
            elif guard_name == "DateGuard":
                date_context = {"current_date": f"2024-{episode_num:02d}-01"}
                guard.check(date_context, episode_num)
            elif guard_name == "AnchorGuard":
                guard.check(draft, episode_num)
            elif guard_name == "RuleGuard":
                guard.check(draft)
            elif guard_name == "RelationGuard":
                guard.check(episode_num)
            elif guard_name == "PacingGuard":
                # Simple scene segmentation for pacing analysis
                scene_texts = [
                    draft[: len(draft) // 3],
                    draft[len(draft) // 3 : 2 * len(draft) // 3],
                    draft[2 * len(draft) // 3 :],
                ]
                guard.check(scene_texts, episode_num)
            elif guard_name == "CritiqueGuard":
                guard.check(draft)
            else:
                print(f"⚠️  Unknown guard: {guard_name}")
                continue

            print(f"✅ {guard_name}: PASSED")
        except RetryException as e:
            # In main pipeline, we show warnings but don't halt execution
            print(f"⚠️  {guard_name} Warning: {e}")
        except Exception as e:
            print(f"⚠️  {guard_name} Error: {e}")


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
    # Enable fast mode for unit tests to avoid LLM retry delays
    import os

    if os.getenv("UNIT_TEST_MODE") == "1":
        os.environ.setdefault("FAST_MODE", "1")

    # Step 1: Arc Outliner - create basic arc info
    create_arc_outline(episode_num)

    # Step 2: Beat Planner - generate beats (take first 3 for simplified version)
    all_beats = plan_beats(episode_num, [], return_flat=True)  # Get flat list
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
    import os

    from src.draft_generator import build_prompt, generate_draft  # 기존 placeholder 함수
    from src.llm.gemini_client import GeminiClient

    prompt = build_prompt(
        context=context,
        episode_number=episode_num,
        prev_summary="",
        anchor_goals="",
        style=None,
        max_tokens=3500,
    )

    if os.getenv("UNIT_TEST_MODE") == "1" or os.getenv("GOOGLE_API_KEY") is None:
        draft = generate_draft(context, episode_num)  # 빠른 더미
    else:
        draft = GeminiClient().generate(prompt)  # 실제 초안

    # Step 5.5: Vector Store - save scene embeddings
    try:
        from src.embedding.vector_store import VectorStore

        vector_store = VectorStore(project)

        # Save embeddings for each scene
        for i, scene in enumerate(all_scenes):
            scene_id = f"ep{episode_num:03d}_scene{i+1:03d}"
            scene_text = scene["desc"]

            success = vector_store.add(scene_id, scene_text)
            if success:
                print(f"✅ Saved embedding for scene {scene_id}")
            else:
                print(f"⚠️  Failed to save embedding for scene {scene_id}")

        # Save episode draft embedding
        vector_store.add(f"ep{episode_num:03d}_draft", draft)

    except Exception as e:
        print(f"⚠️  Vector Store Warning: {e}")

    # Step 6: Guard Chain - Quality checks using auto-registry
    print("🛡️  Running Guard Chain (Auto-Registry)...")
    run_guards_auto_registry(draft, episode_num, project)

    # Add context information to the result
    context_summary = f"Generated from {len(scene_descriptions)} scenes across {len(beats)} beats ({len(draft)} characters)"
    context_line = f"\nContext used:\n{context_summary}\n"
    result = f"{draft}{context_line}"

    return result


# CLI setup
app = typer.Typer(help="Final Engine - Integration Pipeline", no_args_is_help=True)


@app.command()
def run(
    episode: int = typer.Option(1, "--episode", help="Episode number to generate"),
    project_id: str = typer.Option("default", "--project-id", help="Project ID for the story"),
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
