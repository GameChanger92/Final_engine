"""
Integration tests for the complete pipeline.

Tests the end-to-end functionality from Arc Outliner through Draft Generator.
"""

import pytest
import time
from pathlib import Path
import sys

# Add src to path so we can import modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from src.main import run_pipeline


def test_pipeline_execution_time():
    """Test that the complete pipeline executes in less than 5 seconds."""
    import os

    # Set environment variable to enable fast mode
    os.environ["UNIT_TEST_MODE"] = "1"

    try:
        start_time = time.time()

        # Run the pipeline
        result = run_pipeline(1)

        end_time = time.time()
        execution_time = end_time - start_time

        # Verify execution time is under 5 seconds
        assert (
            execution_time < 5.0
        ), f"Pipeline took {execution_time:.2f} seconds, should be < 5 seconds"

        # Verify we got a result
        assert isinstance(result, str)
        assert len(result) > 0
    finally:
        # Clean up environment variable
        if "UNIT_TEST_MODE" in os.environ:
            del os.environ["UNIT_TEST_MODE"]


def test_output_file_creation():
    """Test that projects/default/outputs/episode_1.txt is created and contains expected content."""
    # Clean up any existing file
    output_file = Path("projects/default/outputs/episode_1.txt")
    if output_file.exists():
        output_file.unlink()

    # Run the CLI command using subprocess to test the full CLI functionality
    import subprocess

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "src.main",
            "run",
            "--episode",
            "1",
            "--project-id",
            "default",
        ],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent.parent,
    )

    # Verify command succeeded
    assert result.returncode == 0, f"Command failed: {result.stderr}"

    # Verify output file exists
    assert (
        output_file.exists()
    ), "projects/default/outputs/episode_1.txt was not created"

    # Read and verify file content
    content = output_file.read_text(encoding="utf-8")

    # Verify file contains PLACEHOLDER text
    assert "PLACEHOLDER" in content, "Output file should contain PLACEHOLDER text"

    # Verify it contains episode information
    assert "Episode 1" in content, "Output file should contain episode number"

    # Verify file is not empty
    assert len(content) > 0, "Output file should not be empty"


def test_output_directory_creation():
    """Test that the output directory is automatically created."""
    # Remove output directory if it exists
    output_dir = Path("projects/default/outputs")
    if output_dir.exists():
        import shutil

        shutil.rmtree(output_dir)

    # Verify directory doesn't exist
    assert not output_dir.exists(), "Output directory should not exist initially"

    # Run pipeline
    run_pipeline(1, "default")

    # Run CLI to create file
    import subprocess

    subprocess.run(
        [
            sys.executable,
            "-m",
            "src.main",
            "run",
            "--episode",
            "1",
            "--project-id",
            "default",
        ],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent.parent,
    )

    # Verify directory was created
    assert output_dir.exists(), "Output directory should be created automatically"
    assert output_dir.is_dir(), "Output path should be a directory"

    # Verify file was created in the directory
    output_file = output_dir / "episode_1.txt"
    assert output_file.exists(), "Episode file should be created in output directory"


def test_pipeline_content_structure():
    """Test that the pipeline generates content with expected structure."""
    result = run_pipeline(42)  # Use different episode number

    # Verify basic structure
    assert "Episode 42" in result, "Should contain episode number"
    assert "[PLACEHOLDER DRAFT CONTENT]" in result, "Should contain placeholder content"
    assert "Context used:" in result, "Should mention context usage"
    assert "characters" in result, "Should mention character count"

    # Verify it's a multi-line string
    lines = result.split("\n")
    assert len(lines) > 1, "Output should be multi-line"


def test_different_episode_numbers():
    """Test that the pipeline works with different episode numbers."""
    episodes = [1, 5, 10, 100]

    for ep_num in episodes:
        result = run_pipeline(ep_num)

        # Verify episode number is included
        assert f"Episode {ep_num}" in result, f"Should contain episode number {ep_num}"

        # Verify basic content is present
        assert (
            "PLACEHOLDER" in result
        ), f"Episode {ep_num} should contain placeholder content"
        assert len(result) > 0, f"Episode {ep_num} should not be empty"


if __name__ == "__main__":
    pytest.main([__file__])
