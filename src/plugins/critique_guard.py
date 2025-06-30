"""
critique_guard.py

Self-Critique Guard for Final Engine - LLM-powered fun & logic evaluation.

Uses Gemini 2.5 Pro to evaluate generated content for entertainment value
and logical consistency, raising RetryException for low-quality content.
"""

import os
import json
import logging
from typing import Dict, Any
from dotenv import load_dotenv

from src.exceptions import RetryException

# Load environment variables
load_dotenv(".env", override=True)

logger = logging.getLogger(__name__)


class CritiqueGuard:
    """
    Self-Critique Guard - evaluates text quality using LLM-based scoring.

    Uses Gemini 2.5 Pro to score text on fun (entertainment/engagement) and 
    logic (plausibility/coherence) dimensions, raising RetryException if 
    scores fall below threshold.
    """

    def __init__(self, min_score: float = 7.0):
        """
        Initialize CritiqueGuard with minimum score threshold.

        Parameters
        ----------
        min_score : float, optional
            Minimum score threshold (1-10), defaults to 7.0.
            Text with min(fun, logic) < min_score will trigger retry.
        """
        self.min_score = min_score

    def _call_gemini_critique(self, text: str) -> Dict[str, Any]:
        """
        Call Gemini 2.5 Pro to evaluate text quality.

        Parameters
        ----------
        text : str
            Text to evaluate

        Returns
        -------
        Dict[str, Any]
            JSON response with fun, logic scores and comment

        Raises
        ------
        RetryException
            If API call fails or returns invalid format
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
                    "Google Generative AI library not available", 
                    guard_name="critique_guard"
                )

            # Configure the API
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                logger.error("GOOGLE_API_KEY not found in environment")
                raise RetryException(
                    "API key not configured", guard_name="critique_guard"
                )

            genai.configure(api_key=api_key)

            # Get model name from environment
            model_name = os.getenv("MODEL_NAME", "gemini-2.5-pro")

            # Create the model
            model = genai.GenerativeModel(model_name)

            # Configure generation parameters as specified
            generation_config = {
                "temperature": 0.2,
                "max_output_tokens": 512,
            }

            # Build the critique prompt
            prompt = f"""{text}

----
당신은 프로 소설 감정단입니다. 1~10점으로
  • 재미(흥미·몰입)  
  • 개연성(설정·인과)  
을 평가하고 JSON 으로만 답하세요: {{"fun": n, "logic": n, "comment": "..."}}"""

            logger.info("⚡ Critique Guard… (temperature=0.2, max_output_tokens=512)")
            logger.info(f"Calling {model_name} for critique evaluation...")

            # Generate content
            response = model.generate_content(prompt, generation_config=generation_config)

            if not response.text:
                raise RetryException(
                    "Empty response from Gemini for critique", 
                    guard_name="critique_guard"
                )

            # Parse JSON response
            try:
                result = json.loads(response.text.strip())
                
                # Validate required fields
                if not all(key in result for key in ["fun", "logic", "comment"]):
                    raise ValueError("Missing required fields in response")
                
                # Validate score ranges
                fun_score = float(result["fun"])
                logic_score = float(result["logic"])
                
                if not (1 <= fun_score <= 10) or not (1 <= logic_score <= 10):
                    raise ValueError("Scores must be between 1 and 10")
                
                result["fun"] = fun_score
                result["logic"] = logic_score
                
                logger.info(f"Critique scores: fun={fun_score:.1f}, logic={logic_score:.1f}")
                return result
                
            except (json.JSONDecodeError, ValueError, KeyError) as e:
                logger.error(f"Invalid JSON response from Gemini: {response.text}")
                raise RetryException(
                    f"Invalid critique response format: {str(e)}", 
                    guard_name="critique_guard"
                )

        except Exception as e:
            if isinstance(e, RetryException):
                raise
            logger.error(f"Critique LLM call failed: {e}")
            raise RetryException(
                f"Critique evaluation failed: {str(e)}", 
                guard_name="critique_guard"
            )

    def check(self, text: str) -> Dict[str, Any]:
        """
        Check text quality using LLM critique evaluation.

        Parameters
        ----------
        text : str
            Text to evaluate for fun and logic scores

        Returns
        -------
        Dict[str, Any]
            Results containing critique scores and evaluation details

        Raises
        ------
        RetryException
            If scores fall below minimum threshold
        """
        results = {
            "passed": True,
            "fun_score": None,
            "logic_score": None,
            "comment": None,
            "min_score": self.min_score,
            "flags": {}
        }

        try:
            # Get critique evaluation from Gemini
            critique = self._call_gemini_critique(text)
            
            fun_score = critique["fun"]
            logic_score = critique["logic"]
            comment = critique["comment"]
            
            results["fun_score"] = fun_score
            results["logic_score"] = logic_score
            results["comment"] = comment
            
            # Check if scores meet minimum threshold
            min_actual_score = min(fun_score, logic_score)
            
            if min_actual_score < self.min_score:
                results["passed"] = False
                
                # Create flags for RetryException
                flags = {
                    "critique_failure": {
                        "fun_score": fun_score,
                        "logic_score": logic_score,
                        "min_score": self.min_score,
                        "comment": comment,
                    }
                }
                results["flags"] = flags
                
                # Raise exception for retry
                message = (
                    f"Critique scores too low: fun={fun_score:.1f}, "
                    f"logic={logic_score:.1f} (min={self.min_score:.1f}). "
                    f"Comment: {comment}"
                )
                raise RetryException(
                    message=message, 
                    flags=flags, 
                    guard_name="critique_guard"
                )
            
            logger.info(f"Self-Critique PASS (fun={fun_score:.1f},logic={logic_score:.1f})")
            return results
            
        except RetryException:
            # Re-raise RetryException
            raise
        except Exception as e:
            logger.error(f"Unexpected error in critique guard: {e}")
            raise RetryException(
                f"Critique guard error: {str(e)}", 
                guard_name="critique_guard"
            )


def check_critique_guard(text: str, min_score: float = None) -> Dict[str, Any]:
    """
    Convenience function to run critique guard check.

    Parameters
    ----------
    text : str
        Text to analyze for quality
    min_score : float, optional
        Minimum score threshold. If None, uses environment variable 
        MIN_CRITIQUE_SCORE or defaults to 7.0

    Returns
    -------
    Dict[str, Any]
        Results containing critique evaluation details

    Raises
    ------
    RetryException
        If critique scores fall below threshold
    """
    if min_score is None:
        min_score = float(os.getenv("MIN_CRITIQUE_SCORE", "7.0"))
    
    guard = CritiqueGuard(min_score=min_score)
    return guard.check(text)


def critique_guard(text: str, *, min_score: float = 7.0) -> None:
    """
    Main entry point for critique guard check.

    Parameters
    ----------
    text : str
        Text to evaluate for quality
    min_score : float, optional
        Minimum score threshold (1-10), defaults to 7.0.
        Uses environment variable MIN_CRITIQUE_SCORE if available.

    Raises
    ------
    RetryException
        If critique scores fall below minimum threshold
    """
    # Use environment variable if available, otherwise use provided min_score
    env_min_score = os.getenv("MIN_CRITIQUE_SCORE")
    if env_min_score is not None:
        min_score = float(env_min_score)
    
    try:
        check_critique_guard(text, min_score)
    except RetryException:
        # Re-raise the exception to be handled by the caller
        raise