"""
draft_generator.py

임시(placeholder) 버전:
컨텍스트와 에피소드 번호를 받아서 더미 텍스트를 반환합니다.
나중에 실제 LLM 호출 로직으로 교체할 예정입니다.
"""

import typer


def generate_draft(context: str, episode_num: int) -> str:
    """
    Generate a draft episode based on context and episode number.

    Parameters
    ----------
    context : str
        Context information for the episode
    episode_num : int
        Episode number

    Returns
    -------
    str
        Generated draft text (placeholder implementation)
    """
    lines = [
        f"=== Episode {episode_num} Draft ===",
        "",
        "[PLACEHOLDER DRAFT CONTENT]",
        "",
        f"Context used: {len(context)} characters",
        "",
        "This is a stub implementation that will be replaced",
        "with actual LLM-generated content in the future.",
        "",
        f"Episode {episode_num} - Generated draft complete.",
    ]

    return "\n".join(lines)


# CLI setup
app = typer.Typer(
    help="Draft Generator - Generate episode drafts from context", no_args_is_help=True
)


@app.command()
def run_draft(
    context: str = typer.Option(
        "Default context", "--context", help="Context for draft generation"
    ),
    episode_num: int = typer.Option(1, "--episode", help="Episode number"),
):
    """
    Generate and display a draft for the given context and episode number.
    """
    typer.echo(f"Generating draft for episode {episode_num}...")

    draft = generate_draft(context, episode_num)

    typer.echo("\n" + "=" * 50)
    typer.echo(draft)
    typer.echo("=" * 50 + "\n")

    typer.echo("Draft generation completed successfully.")


@app.command()
def info():
    """
    Display information about the draft generator.
    """
    typer.echo("Draft Generator v1.0 - Stub Implementation")
    typer.echo(
        "Generates placeholder draft content based on context and episode number"
    )
    typer.echo("Will be replaced with actual LLM implementation in the future")


if __name__ == "__main__":
    app()
