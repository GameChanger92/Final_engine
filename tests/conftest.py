"""
conftest.py

Global test configuration for Final Engine test suite.
Provides shared fixtures and test project configuration.
"""

import pytest
from pathlib import Path
import json


PROJECT_ID = "test_proj"


@pytest.fixture(scope="session")
def project_id():
    """Provide test project ID for all tests."""
    return PROJECT_ID


@pytest.fixture(scope="session", autouse=True)
def setup_test_project():
    """
    Set up test project structure at session start.
    Creates a test project with minimal required data files.
    """
    # Create test project directory structure
    test_proj_dir = Path("projects") / PROJECT_ID
    data_dir = test_proj_dir / "data"
    outputs_dir = test_proj_dir / "outputs"

    # Ensure directories exist
    data_dir.mkdir(parents=True, exist_ok=True)
    outputs_dir.mkdir(parents=True, exist_ok=True)

    # Create minimal data files for testing if they don't exist

    # anchors.json
    anchors_file = data_dir / "anchors.json"
    if not anchors_file.exists():
        anchors_data = [
            {"id": "ANCHOR_01", "goal": "주인공 등장", "anchor_ep": 1},
            {"id": "ANCHOR_02", "goal": "첫 번째 갈등", "anchor_ep": 5},
            {"id": "ANCHOR_03", "goal": "중요한 만남", "anchor_ep": 10},
        ]
        with open(anchors_file, "w", encoding="utf-8") as f:
            json.dump(anchors_data, f, ensure_ascii=False, indent=2)

    # characters.json
    characters_file = data_dir / "characters.json"
    if not characters_file.exists():
        characters_data = {
            "main_character": {
                "name": "TestCharacter",
                "role": "protagonist",
                "traits": ["brave", "intelligent"],
                "immutable": ["name", "role"],
            }
        }
        with open(characters_file, "w", encoding="utf-8") as f:
            json.dump(characters_data, f, ensure_ascii=False, indent=2)

    # rules.json
    rules_file = data_dir / "rules.json"
    if not rules_file.exists():
        rules_data = [
            {"pattern": "forbidden_word", "message": "Forbidden word detected"}
        ]
        with open(rules_file, "w", encoding="utf-8") as f:
            json.dump(rules_data, f, ensure_ascii=False, indent=2)

    # episode_dates.json
    dates_file = data_dir / "episode_dates.json"
    if not dates_file.exists():
        dates_data = {}
        with open(dates_file, "w", encoding="utf-8") as f:
            json.dump(dates_data, f, ensure_ascii=False, indent=2)

    # foreshadow.json
    foreshadow_file = data_dir / "foreshadow.json"
    if not foreshadow_file.exists():
        foreshadow_data = {"foreshadows": []}
        with open(foreshadow_file, "w", encoding="utf-8") as f:
            json.dump(foreshadow_data, f, ensure_ascii=False, indent=2)

    yield

    # Cleanup after session (optional - leave files for debugging)
    # if test_proj_dir.exists():
    #     shutil.rmtree(test_proj_dir)
