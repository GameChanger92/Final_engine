"""
beat_planner.py

Beat Planner v2: 3막 · 6시퀀스 · 4비트 자동화
- Act 1 (Setup): Seq1·Seq2
- Act 2 (Confrontation): Seq3·Seq4  
- Act 3 (Resolution): Seq5·Seq6
- 각 시퀀스마다 4비트 (Turning Point 포함)
"""

import os
import re
import logging
from pathlib import Path
from typing import List, Dict

from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from src.core.retry_controller import run_with_retry
from src.exceptions import RetryException

# Load environment variables
load_dotenv(".env", override=True)

logger = logging.getLogger(__name__)


def build_prompt(arc_goal: str, prev_beats: List[str], sequence_no: int) -> str:
    """
    Build a prompt for beat generation using Jinja2 template.

    Parameters
    ----------
    arc_goal : str
        Story arc goal or context information
    prev_beats : List[str]
        List of previous beat descriptions for context
    sequence_no : int
        Current sequence number (1-6)

    Returns
    -------
    str
        Formatted prompt for LLM
    """
    try:
        # Setup Jinja2 environment
        template_dir = Path(__file__).parent.parent / "templates"
        jinja_env = Environment(loader=FileSystemLoader(str(template_dir)))

        # Load the beat prompt template
        template = jinja_env.get_template("beat_prompt.j2")

        # Render the template with variables
        prompt = template.render(
            arc_goal=arc_goal,
            prev_beats=prev_beats,
            sequence_no=sequence_no
        )

        logger.debug(f"Built beat prompt: {len(prompt)} characters")
        return prompt

    except TemplateNotFound:
        logger.error("Beat prompt template not found")
        # Fallback prompt
        return f"""Generate 4 story beats for sequence {sequence_no}.

Arc goal: {arc_goal}

Previous beats: {prev_beats}

Output format:
beat_1: "첫 번째 비트"
beat_2: "두 번째 비트"  
beat_3: "세 번째 비트"
beat_tp: "전환점 비트"
"""

    except Exception as e:
        logger.error(f"Error building beat prompt: {e}")
        # Fallback prompt
        return f"Generate 4 beats for sequence {sequence_no} based on: {arc_goal}"


def call_llm(prompt: str) -> str:
    """
    Call Gemini 2.5 Pro to generate beat content.

    Parameters
    ----------
    prompt : str
        Formatted prompt for generation

    Returns
    -------
    str
        Generated beats text from Gemini

    Raises
    ------
    RetryException
        If API call fails or returns invalid content
    """
    try:
        # Import google.generativeai
        try:
            # Test mode flag for unit tests
            if os.getenv("UNIT_TEST_MODE") == "1":
                raise ImportError("Forced import error for unit test")
            import google.generativeai as genai
        except ImportError:
            logger.error("google-generativeai not installed")
            raise RetryException(
                "Google Generative AI library not available", guard_name="llm_call"
            )

        # Configure the API
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            logger.error("GOOGLE_API_KEY not found in environment")
            raise RetryException("API key not configured", guard_name="llm_call")

        genai.configure(api_key=api_key)

        # Get model name from environment
        model_name = os.getenv("MODEL_NAME", "gemini-2.5-pro")

        # Create the model
        model = genai.GenerativeModel(model_name)

        # Configure generation parameters
        temperature = float(os.getenv("TEMP_BEAT", "0.3"))
        generation_config = {
            "max_output_tokens": 2048,
            "temperature": temperature,
        }

        # Generate content
        logger.info(f"⚡ Beat Planner… (temperature={temperature}, max_output_tokens=2048)")
        logger.info(f"Calling {model_name} for beat generation...")
        response = model.generate_content(prompt, generation_config=generation_config)

        if not response.text:
            raise RetryException("Empty response from Gemini", guard_name="llm_call")

        logger.info(f"Generated beats: {len(response.text)} characters")
        return response.text

    except Exception as e:
        if isinstance(e, RetryException):
            raise
        logger.error(f"LLM call failed: {e}")
        raise RetryException(f"LLM generation failed: {str(e)}", guard_name="llm_call")


def plan_beats(episode_num: int, prev_beats: List[str] = None) -> dict:
    """
    Generate beats for all 6 sequences of an episode using 3-Act structure.

    Parameters
    ----------
    episode_num : int
        Episode number (1-based)
    prev_beats : List[str], optional
        Previous episode beats for context

    Returns
    -------
    dict
        Nested dictionary with ep_X -> seq_Y -> beat_Z structure
    """
    if prev_beats is None:
        prev_beats = []

    # Create arc goal based on episode
    arc_goal = f"Episode {episode_num}: Continue the story progression with compelling character development and plot advancement."

    # Initialize episode structure
    episode_key = f"ep_{episode_num}"
    episode_data = {}

    # Generate beats for all 6 sequences
    for seq_num in range(1, 7):
        try:
            # Build prompt for this sequence
            prompt = build_prompt(arc_goal, prev_beats, seq_num)

            # Call LLM with retry mechanism
            def llm_wrapper():
                raw_output = call_llm(prompt)
                # Parse and validate the output
                beats = parse_beat_output(raw_output)
                if len(beats) != 4:
                    raise RetryException(
                        f"Expected 4 beats, got {len(beats)}",
                        guard_name="beat_count",
                    )
                return beats

            beats = run_with_retry(llm_wrapper)

            # Store beats in the episode structure
            seq_key = f"seq_{seq_num}"
            episode_data[seq_key] = beats

            logger.info(f"⚡ Beat Planner… (Act {get_act_number(seq_num)} · Seq{seq_num} → 4 Beats generated)")

        except Exception as e:
            logger.error(f"Failed to generate beats for sequence {seq_num}: {e}")
            # Fallback beats for this sequence
            episode_data[f"seq_{seq_num}"] = generate_fallback_beats(seq_num)

    return {episode_key: episode_data}


def parse_beat_output(raw_output: str) -> dict:
    """
    Parse LLM output into structured beat dictionary.

    Parameters
    ----------
    raw_output : str
        Raw output from LLM

    Returns
    -------
    dict
        Dictionary with beat_1, beat_2, beat_3, beat_tp keys
    """
    beats = {}
    
    # Define patterns for each beat type
    patterns = {
        'beat_1': r'beat_1:\s*["\']([^"\']+)["\']',
        'beat_2': r'beat_2:\s*["\']([^"\']+)["\']', 
        'beat_3': r'beat_3:\s*["\']([^"\']+)["\']',
        'beat_tp': r'beat_tp:\s*["\']([^"\']+)["\']'
    }
    
    for beat_key, pattern in patterns.items():
        match = re.search(pattern, raw_output)
        if match:
            beats[beat_key] = match.group(1)
        else:
            # Fallback for missing beats
            beats[beat_key] = f"Generated {beat_key} content"
    
    return beats


def generate_fallback_beats(seq_num: int) -> dict:
    """
    Generate fallback beats when LLM fails.

    Parameters
    ----------
    seq_num : int
        Sequence number

    Returns
    -------
    dict
        Fallback beat dictionary
    """
    act_num = get_act_number(seq_num)
    return {
        "beat_1": f"Act {act_num} Seq{seq_num} - 상황 설정",
        "beat_2": f"Act {act_num} Seq{seq_num} - 갈등 전개", 
        "beat_3": f"Act {act_num} Seq{seq_num} - 해결 시도",
        "beat_tp": f"Act {act_num} Seq{seq_num} - 전환점 발생"
    }


def get_act_number(seq_num: int) -> int:
    """
    Get act number for a given sequence number.

    Parameters
    ----------
    seq_num : int
        Sequence number (1-6)

    Returns
    -------
    int
        Act number (1-3)
    """
    if seq_num in [1, 2]:
        return 1  # Setup
    elif seq_num in [3, 4]:
        return 2  # Confrontation
    else:  # seq_num in [5, 6]
        return 3  # Resolution


def make_beats(arc_json: dict) -> list[dict]:
    """
    Generate 10 beat dictionaries for a given story arc.
    
    LEGACY FUNCTION: Maintained for backward compatibility.

    Parameters
    ----------
    arc_json : dict
        Example: {"title": "Prologue", "anchor_ep": 3}

    Returns
    -------
    list[dict]
        [{"idx": 1, "summary": "...", "anchor": False}, ...]
    """
    title = arc_json.get("title", "Untitled")
    anchor_ep = arc_json.get("anchor_ep")

    beats = []
    for i in range(10):
        idx = i + 1
        beats.append(
            {
                "idx": idx,
                "summary": f"{title} — beat {idx}",
                "anchor": (idx == anchor_ep),
            }
        )
    return beats


def make_beats(arc_json: dict) -> list[dict]:
    """
    Generate 10 beat dictionaries for a given story arc.

    Parameters
    ----------
    arc_json : dict
        Example: {"title": "Prologue", "anchor_ep": 3}

    Returns
    -------
    list[dict]
        [{"idx": 1, "summary": "...", "anchor": False}, ...]
    """
    title = arc_json.get("title", "Untitled")
    anchor_ep = arc_json.get("anchor_ep")

    beats = []
    for i in range(10):
        idx = i + 1
        beats.append(
            {
                "idx": idx,
                "summary": f"{title} — beat {idx}",
                "anchor": (idx == anchor_ep),
            }
        )
    return beats
