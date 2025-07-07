"""
Test for the anchor-driven integration test script.

Tests both success and failure scenarios for the anchor flow validation.
"""

import json
import os
import subprocess
import tempfile
from pathlib import Path


def get_test_env():
    """Get environment variables for test mode."""
    test_env = os.environ.copy()
    test_env["UNIT_TEST_MODE"] = "1"
    test_env["FAST_MODE"] = "1"
    return test_env


class TestAnchorFlow:
    """Test class for anchor flow integration test."""

    def setup_method(self):
        """Set up test environment."""
        self.script_path = Path(__file__).parent.parent.parent / "scripts" / "run_anchor_flow.py"
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up test environment."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_test_anchors(self, anchors_data):
        """Create a temporary anchors.json file."""
        anchors_path = os.path.join(self.temp_dir, "test_anchors.json")
        with open(anchors_path, "w", encoding="utf-8") as f:
            json.dump(anchors_data, f, ensure_ascii=False, indent=2)
        return anchors_path

    def test_anchor_flow_success_with_five_anchors(self):
        """Test that the script succeeds when all 5 anchors are properly configured."""
        # Create 5 test anchors spread across episodes
        test_anchors = [
            {"id": "ANCHOR_01", "goal": "주인공 첫 등장", "anchor_ep": 1},
            {"id": "ANCHOR_02", "goal": "첫 번째 시련", "anchor_ep": 5},
            {"id": "ANCHOR_03", "goal": "중요한 만남", "anchor_ep": 10},
            {"id": "ANCHOR_04", "goal": "결정적 선택", "anchor_ep": 15},
            {"id": "ANCHOR_05", "goal": "마지막 대결", "anchor_ep": 20},
        ]

        anchors_path = self.create_test_anchors(test_anchors)

        # Run the script with test anchors
        result = subprocess.run(
            ["python", str(self.script_path), "--anchors", anchors_path],
            capture_output=True,
            text=True,
            cwd=self.script_path.parent.parent,
            env=get_test_env(),
        )

        # Should succeed with all anchors found
        assert (
            result.returncode == 0
        ), f"Script failed with output: {result.stdout}\n{result.stderr}"
        assert "TEST RESULT: PASS" in result.stdout
        assert "All anchor events were found" in result.stdout
        assert "SUCCESS: All anchor events validated!" in result.stdout

    def test_anchor_flow_handles_missing_anchors_file(self):
        """Test script behavior when anchors file is missing."""
        non_existent_path = os.path.join(self.temp_dir, "missing.json")

        result = subprocess.run(
            ["python", str(self.script_path), "--anchors", non_existent_path],
            capture_output=True,
            text=True,
            cwd=self.script_path.parent.parent,
            env=get_test_env(),
        )

        # Should fail gracefully when no anchors file exists
        assert result.returncode == 1
        assert "ERROR: No anchors found" in result.stdout

    def test_anchor_flow_with_empty_anchors(self):
        """Test script behavior with empty anchors file."""
        anchors_path = self.create_test_anchors([])

        result = subprocess.run(
            ["python", str(self.script_path), "--anchors", anchors_path],
            capture_output=True,
            text=True,
            cwd=self.script_path.parent.parent,
            env=get_test_env(),
        )

        # Should fail when no anchors are defined
        assert result.returncode == 1
        assert "ERROR: No anchors found" in result.stdout

    def test_anchor_flow_script_exists_and_executable(self):
        """Test that the script file exists and is executable."""
        assert self.script_path.exists(), f"Script not found at {self.script_path}"
        assert os.access(self.script_path, os.X_OK), f"Script not executable: {self.script_path}"

    def test_anchor_flow_help_option(self):
        """Test that the script provides help information."""
        result = subprocess.run(
            ["python", str(self.script_path), "--help"],
            capture_output=True,
            text=True,
            cwd=self.script_path.parent.parent,
            env=get_test_env(),
        )

        assert result.returncode == 0
        assert "anchor-driven integration flow" in result.stdout
        assert "--anchors" in result.stdout

    def test_script_validates_anchor_count(self):
        """Test that script reports correct number of anchors found."""
        # Create exactly 3 anchors to test counting
        test_anchors = [
            {"id": "ANCHOR_01", "goal": "주인공 첫 등장", "anchor_ep": 1},
            {"id": "ANCHOR_02", "goal": "첫 번째 시련", "anchor_ep": 5},
            {"id": "ANCHOR_03", "goal": "중요한 만남", "anchor_ep": 10},
        ]

        anchors_path = self.create_test_anchors(test_anchors)

        result = subprocess.run(
            ["python", str(self.script_path), "--anchors", anchors_path],
            capture_output=True,
            text=True,
            cwd=self.script_path.parent.parent,
            env=get_test_env(),
        )

        # Should succeed and report correct count
        assert result.returncode == 0
        assert "Loaded 3 anchor events:" in result.stdout
        assert "Anchors Found (3/3):" in result.stdout

    def test_default_anchors_file_usage(self):
        """Test that script uses default anchors.json when no file specified."""
        # Run script without --anchors flag (should use data/anchors.json)
        result = subprocess.run(
            ["python", str(self.script_path)],
            capture_output=True,
            text=True,
            cwd=self.script_path.parent.parent,
            env=get_test_env(),
        )

        # Should run successfully with default anchors
        assert result.returncode == 0
        assert "Loaded 5 anchor events:" in result.stdout
