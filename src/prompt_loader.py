"""
prompt_loader.py

Prompt and style configuration loader for Final Engine.
Loads platform-specific styles from templates/style_configs/ directory.
"""

import json
import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def load_style(platform: str | None = None) -> dict[str, Any]:
    """
    Load style configuration for the specified platform.

    Parameters
    ----------
    platform : str, optional
        Platform name (munpia, kakao, etc.). If None, uses PLATFORM env var.
        If platform not found, defaults to munpia.

    Returns
    -------
    Dict[str, Any]
        Style configuration dictionary with tone, voice_main, voice_side, etc.
    """
    # Get platform from parameter or environment variable
    if platform is None:
        platform = os.getenv("PLATFORM", "munpia")

    # Get the style configs directory path
    style_configs_dir = Path(__file__).parent.parent / "templates" / "style_configs"
    style_file_path = style_configs_dir / f"{platform}.json"

    # Try to load the requested platform style
    if style_file_path.exists():
        try:
            with open(style_file_path, encoding="utf-8") as f:
                style_config = json.load(f)
                logger.info(f"Loaded style: {platform}")
                return style_config
        except (json.JSONDecodeError, OSError) as e:
            logger.error(f"Error loading style config for {platform}: {e}")
    else:
        logger.warning(f"Style config not found for platform: {platform}")

    # Fallback to munpia if the requested platform fails or doesn't exist
    fallback_platform = "munpia"
    if platform != fallback_platform:
        fallback_path = style_configs_dir / f"{fallback_platform}.json"
        if fallback_path.exists():
            try:
                with open(fallback_path, encoding="utf-8") as f:
                    style_config = json.load(f)
                    logger.info(f"Loaded fallback style: {fallback_platform}")
                    return style_config
            except (json.JSONDecodeError, OSError) as e:
                logger.error(f"Error loading fallback style config: {e}")

    # Final fallback with hardcoded default values
    logger.warning("Using hardcoded default style configuration")
    return {
        "platform": "default",
        "tone": "균형 잡힌",
        "voice_main": "3인칭 관찰자",
        "voice_side": "표준형",
        "enter_rule": "문단별 줄바꿈",
        "prompt_suffix": "일반적인 소설 형식으로 작성해주세요.",
    }


def get_available_platforms() -> list[str]:
    """
    Get list of available platform configurations.

    Returns
    -------
    list[str]
        List of available platform names
    """
    style_configs_dir = Path(__file__).parent.parent / "templates" / "style_configs"

    if not style_configs_dir.exists():
        return []

    platforms = []
    for json_file in style_configs_dir.glob("*.json"):
        platform_name = json_file.stem
        platforms.append(platform_name)

    return sorted(platforms)
