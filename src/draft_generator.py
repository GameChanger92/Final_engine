"""
draft_generator.py

임시(placeholder) 버전:
컨텍스트 문자열을 받아서 플레이스홀더 에피소드 드래프트를 반환합니다.
나중에 실제 LLM 호출 로직으로 교체할 예정입니다.
"""

import pathlib
from typing import Optional
import typer


def generate_draft(context: str, episode_num: int = 1) -> str:
    """
    Generate a placeholder draft for an episode.

    Parameters
    ----------
    context : str
        The context string to use for draft generation
    episode_num : int, optional
        The episode number, by default 1

    Returns
    -------
    str
        Formatted placeholder draft with episode number and truncated context
    """
    # Truncate context to 200 characters and add ellipsis if needed
    truncated_context = context[:200]
    if len(context) > 200:
        truncated_context += "..."

    return f"PLACEHOLDER EPISODE {episode_num}\n\n{truncated_context}"


# CLI setup
app = typer.Typer(
    help="Draft Generator - Generate episode drafts from context", no_args_is_help=True
)


@app.command()
def run(
    context_file: Optional[str] = typer.Option(
        None, "--context-file", help="Path to context file"
    ),
    context: Optional[str] = typer.Option(
        None, "--context", help="Direct context input"
    ),
    episode: int = typer.Option(1, "--episode", help="Episode number"),
):
    """
    Generate draft from context file or direct input.
    """
    # Validate that exactly one of context_file or context is provided
    if context_file and context:
        typer.echo("Error: Cannot specify both --context-file and --context", err=True)
        raise typer.Exit(1)

    if not context_file and not context:
        typer.echo("Error: Must specify either --context-file or --context", err=True)
        raise typer.Exit(1)

    # Get context from file or direct input
    if context_file:
        try:
            context_text = pathlib.Path(context_file).read_text(encoding="utf-8")
        except FileNotFoundError:
            typer.echo(f"Error: File '{context_file}' not found", err=True)
            raise typer.Exit(1)
        except Exception as e:
            typer.echo(f"Error reading file '{context_file}': {e}", err=True)
            raise typer.Exit(1)
    else:
        context_text = context

    # Generate draft
    draft = generate_draft(context_text, episode)

    # Display result
    typer.echo(draft)


@app.command()
def info():
    """
    Display information about the draft generator.
    """
    typer.echo("Draft Generator v1.0 - Stub Implementation")
    typer.echo("Generates placeholder episode drafts with context truncation")


if __name__ == "__main__":
    app()
