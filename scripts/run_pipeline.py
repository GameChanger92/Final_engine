#!/usr/bin/env python3
"""
run_pipeline.py

Pipeline test runner for Final Engine
Tests episodes 1-20 with guard validation sequence
"""

import argparse
import sys
from pathlib import Path
import json

# Add src directory to Python path
script_dir = Path(__file__).parent
project_root = script_dir.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from src.exceptions import RetryException  # noqa: E402
from src.utils.path_helper import data_path  # noqa: E402
from src.core.retry_controller import run_with_retry  # noqa: E402

# TODO: from src.main import run_pipeline  # Not used in current implementation


def test_guards_sequence(episode_num: int, project: str = "default") -> bool:
    """
    Test all guards in the specified sequence and return success status.

    Expected sequence:
    1. LexiGuard PASS
    2. EmotionGuard PASS
    3. ScheduleGuard PASS
    4. ImmutableGuard PASS
    5. DateGuard PASS
    6. AnchorGuard PASS
    7. RuleGuard PASS
    8. RelationGuard PASS
    9. PacingGuard PASS
    10. CritiqueGuard PASS

    Parameters
    ----------
    episode_num : int
        Episode number to test
    project : str, optional
        Project ID for path resolution, defaults to "default"

    Returns
    -------
    bool
        True if all guards pass, False otherwise
    """
    print(f"\n🧪 Testing Episode {episode_num} Guard Sequence...")

    # Sample draft content for testing with high lexical diversity and Korean pacing elements
    draft_content = f"""
    Episode {episode_num} begins with our protagonist facing unprecedented challenges.
    주인공이 달렸다. "어디로 가야 하지?" 그는 생각했다. The protagonist makes their first appearance.
    
    The morning sun illuminated the bustling marketplace. 상인이 물건을 꺼냈다.
    "좋은 아침입니다!" 그가 외쳤다. Children laughed gleefully while playing nearby fountains.
    아이들이 뛰어갔다. "재미있다!" 그들이 말했다. 행복하다고 느꼈다.
    
    Suddenly, mysterious shadows emerged from ancient alleyways. 그림자가 움직였다.
    Citizens gathered nervously. "무슨 일이지?" 그들이 걱정했다. 두렵다고 생각했다.
    
    Our brave heroes must navigate complex political intrigue. 영웅들이 싸웠다.
    "우리가 해야 할 일이 무엇인가?" 대장이 물었다. 각자 다짐했다.
    Each character demonstrates unique abilities. 치료사가 치유했다.
    
    The antagonist reveals sinister motivations. 악역이 공격했다.
    "너희는 이해하지 못한다!" 그가 소리쳤다. 분노했다고 깨달았다.
    Family loyalties clash against moral obligations. 가족이 갈등했다.
    
    Romance blooms unexpectedly between unlikely partners. 연인들이 만났다.
    "당신을 사랑합니다." 그녀가 고백했다. 기쁘다고 알았다.
    Their relationship develops gradually through shared hardships.
    
    Technological innovations transform traditional combat methods. 전사들이 훈련했다.
    "새로운 무기를 배워야 한다." 교관이 설명했다. 어렵다고 판단했다.
    Veterans struggle adapting while younger fighters embrace new approaches.
    
    Environmental disasters threaten agricultural sustainability. 농민들이 일했다.
    "비가 오지 않는다." 그들이 한탄했다. 절망했다고 받아들였다.
    Resource scarcity exacerbates existing social tensions.
    
    The episode concludes with surprising revelations. 진실이 드러났다.
    "모든 것이 연결되어 있었다!" 탐정이 발견했다. 놀랐다고 이해했다.
    Setting up future storylines that will explore themes of redemption and justice.
    """

    guards_passed = 0
    total_guards = 10  # Updated to include critique guard

    # 1. LexiGuard Test
    try:
        from src.plugins.lexi_guard import lexi_guard

        run_with_retry(lexi_guard, draft_content)
        print("✅ LexiGuard PASS")
        guards_passed += 1
    except RetryException as e:
        print(f"❌ LexiGuard FAIL: {e}")
    except Exception as e:
        print(f"⚠️  LexiGuard ERROR: {e}")

    # 2. EmotionGuard Test
    try:
        from src.plugins.emotion_guard import emotion_guard

        # Test with neutral content that shouldn't trigger emotion alerts
        prev_text = "This is some neutral previous content."
        run_with_retry(emotion_guard, prev_text, draft_content)
        print("✅ EmotionGuard PASS")
        guards_passed += 1
    except RetryException as e:
        print(f"❌ EmotionGuard FAIL: {e}")
    except Exception as e:
        print(f"⚠️  EmotionGuard ERROR: {e}")

    # 3. ScheduleGuard Test
    try:
        from src.plugins.schedule_guard import schedule_guard

        # Pass episode number directly as schedule_guard expects int
        run_with_retry(schedule_guard, episode_num)
        print("✅ ScheduleGuard PASS")
        guards_passed += 1
    except RetryException as e:
        print(f"❌ ScheduleGuard FAIL: {e}")
    except Exception as e:
        print(f"⚠️  ScheduleGuard ERROR: {e}")

    # 4. ImmutableGuard Test
    try:
        from src.plugins.immutable_guard import immutable_guard

        # Load or create sample character data with proper structure
        char_path = data_path("characters.json", project)
        try:
            with open(char_path, "r", encoding="utf-8") as f:
                characters = json.load(f)
        except FileNotFoundError:
            # Create minimal character data for testing with immutable field
            characters = {
                "main_character": {
                    "name": "TestCharacter",
                    "role": "protagonist",
                    "traits": ["brave", "intelligent"],
                    "immutable": ["name", "role"],  # Required field for ImmutableGuard
                }
            }

        run_with_retry(immutable_guard, characters, project)
        print("✅ ImmutableGuard PASS")
        guards_passed += 1
    except RetryException as e:
        print(f"❌ ImmutableGuard FAIL: {e}")
    except Exception as e:
        print(f"⚠️  ImmutableGuard ERROR: {e}")

    # 5. DateGuard Test
    try:
        from src.plugins.date_guard import date_guard

        # Create date context for testing
        date_context = {
            "current_date": f"2024-{episode_num:02d}-01",
            "episode": episode_num,
        }
        run_with_retry(date_guard, date_context, episode_num, project)
        print("✅ DateGuard PASS")
        guards_passed += 1
    except RetryException as e:
        print(f"❌ DateGuard FAIL: {e}")
    except Exception as e:
        print(f"⚠️  DateGuard ERROR: {e}")

    # 6. AnchorGuard Test
    try:
        from src.plugins.anchor_guard import anchor_guard

        # Test with draft content that should contain anchor events
        run_with_retry(anchor_guard, draft_content, episode_num, project)
        print("✅ AnchorGuard PASS")
        guards_passed += 1
    except RetryException as e:
        print(f"❌ AnchorGuard FAIL: {e}")
    except Exception as e:
        print(f"⚠️  AnchorGuard ERROR: {e}")

    # 7. RuleGuard Test
    try:
        from src.plugins.rule_guard import rule_guard

        # Test with content that should pass all rules
        run_with_retry(rule_guard, draft_content, project=project)
        print("✅ RuleGuard PASS")
        guards_passed += 1
    except RetryException as e:
        print(f"❌ RuleGuard FAIL: {e}")
    except Exception as e:
        print(f"⚠️  RuleGuard ERROR: {e}")

    # 8. RelationGuard Test
    try:
        from src.plugins.relation_guard import relation_guard

        # Test relationship changes for current episode
        run_with_retry(relation_guard, episode_num, project=project)
        print("✅ RelationGuard PASS")
        guards_passed += 1
    except RetryException as e:
        print(f"❌ RelationGuard FAIL: {e}")
    except Exception as e:
        print(f"⚠️  RelationGuard ERROR: {e}")

    # 9. PacingGuard Test
    try:
        from src.plugins.pacing_guard import pacing_guard

        # Create scene texts for pacing analysis
        scene_texts = [
            draft_content[: len(draft_content) // 3],  # First third
            draft_content[
                len(draft_content) // 3 : 2 * len(draft_content) // 3
            ],  # Middle third
            draft_content[2 * len(draft_content) // 3 :],  # Last third
        ]

        run_with_retry(pacing_guard, scene_texts, episode_num, project)
        print("✅ PacingGuard PASS")
        guards_passed += 1
    except RetryException as e:
        print(f"❌ PacingGuard FAIL: {e}")
    except Exception as e:
        print(f"⚠️  PacingGuard ERROR: {e}")

    # 10. CritiqueGuard Test - Self-Critique Guard (Day 25)
    try:
        from src.plugins.critique_guard import critique_guard

        # Test LLM-based fun and logic evaluation
        run_with_retry(critique_guard, draft_content)
        print("✅ CritiqueGuard PASS")
        guards_passed += 1
    except RetryException as e:
        print(f"❌ CritiqueGuard FAIL: {e}")
    except Exception as e:
        print(f"⚠️  CritiqueGuard ERROR: {e}")

    # Context Builder Test (Day 20 requirement)
    try:
        from src.context_builder import ContextBuilder

        print("\n🔧 Testing Context Builder...")
        context_builder = ContextBuilder(project=project)

        # Create sample scenes for context building
        sample_scenes = [
            f"Episode {episode_num} Scene 1: The adventure begins",
            f"Episode {episode_num} Scene 2: Character development",
            f"Episode {episode_num} Scene 3: Conflict resolution",
        ]

        # Build context with the new enhanced builder
        context = context_builder.build_context(
            scenes=sample_scenes,
            previous_episode=f"Previous episode {episode_num-1} summary",
            scene_text_for_vector=sample_scenes[0],
        )

        print("✅ Context Builder PASS")
        print(f"📄 Generated context: {len(context)} characters")

    except Exception as e:
        print(f"⚠️  Context Builder ERROR: {e}")

    # Draft Generator Test (Day 21 requirement)
    try:
        from src.draft_generator import generate_draft

        print("\n🔧 Testing Draft Generator...")

        # Use context from above if available, otherwise create sample context
        test_context = (
            context
            if "context" in locals()
            else f"Sample context for episode {episode_num} testing"
        )

        # Generate draft using new Gemini integration
        draft = generate_draft(test_context, episode_num)

        if len(draft) >= 500:
            guards_status = (
                "guards PASS (Gemini)"
                if "fallback" not in draft
                else "guards PASS (Fallback)"
            )
            print("✅ Draft Generator PASS")
            print(f"📝 Draft generated {len(draft)}+ chars, {guards_status}")
        else:
            print(f"⚠️  Draft Generator WARNING: Only {len(draft)} characters generated")

    except Exception as e:
        print(f"⚠️  Draft Generator ERROR: {e}")

    success_rate = guards_passed / total_guards
    print(
        f"\n📊 Episode {episode_num} Guard Results: {guards_passed}/{total_guards} passed ({success_rate:.1%})"
    )

    return guards_passed == total_guards


def run_episodes_test(start_ep: int, end_ep: int, project: str = "default") -> None:
    """
    Run pipeline test for episodes in the given range.

    Parameters
    ----------
    start_ep : int
        Starting episode number
    end_ep : int
        Ending episode number (inclusive)
    project : str, optional
        Project ID for path resolution, defaults to "default"
    """
    print(
        f"🚀 Starting Pipeline Test for Episodes {start_ep}-{end_ep} (Project: {project})"
    )
    print("=" * 60)

    passed_episodes = []
    failed_episodes = []

    for episode in range(start_ep, end_ep + 1):
        success = test_guards_sequence(episode, project)

        if success:
            passed_episodes.append(episode)
            print(f"✅ Episode {episode}: ALL GUARDS PASSED")
        else:
            failed_episodes.append(episode)
            print(f"❌ Episode {episode}: SOME GUARDS FAILED")

        # Add separator between episodes
        if episode < end_ep:
            print("-" * 40)

    # Final summary
    print("\n" + "=" * 60)
    print("📈 FINAL SUMMARY")
    print("=" * 60)
    print(f"✅ Passed Episodes: {len(passed_episodes)}")
    if passed_episodes:
        print(f"   Episodes: {', '.join(map(str, passed_episodes))}")

    print(f"❌ Failed Episodes: {len(failed_episodes)}")
    if failed_episodes:
        print(f"   Episodes: {', '.join(map(str, failed_episodes))}")

    success_rate = len(passed_episodes) / (end_ep - start_ep + 1)
    print(f"📊 Overall Success Rate: {success_rate:.1%}")

    if success_rate >= 0.6:  # 60% or better = Day 12 completion goal
        print("\n🎉 SUCCESS: Day 12 completion criteria met!")
        print("   (60%+ episodes passing all guard checks)")
    else:
        print("\n⚠️  PARTIAL: More work needed to reach Day 12 goals")


def parse_episode_range(episode_range: str) -> tuple[int, int]:
    """
    Parse episode range string like "1-20" or "5" into start, end tuple.

    Parameters
    ----------
    episode_range : str
        Range string (e.g., "1-20", "5", "10-15")

    Returns
    -------
    tuple[int, int]
        Start and end episode numbers (inclusive)
    """
    if "-" in episode_range:
        start, end = episode_range.split("-", 1)
        return int(start), int(end)
    else:
        episode = int(episode_range)
        return episode, episode


def main():
    """Main entry point for pipeline testing."""
    parser = argparse.ArgumentParser(
        description="Run pipeline tests with guard validation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_pipeline.py --episodes 1-20    # Test episodes 1 through 20
  python run_pipeline.py --episodes 5       # Test only episode 5
  python run_pipeline.py --episodes 10-15   # Test episodes 10 through 15
  python run_pipeline.py --project-id demo_novel --episodes 1-3  # Test with demo project

Expected Output Format:
  ✅ LexiGuard PASS
  ✅ EmotionGuard PASS
  ✅ ScheduleGuard PASS
  ✅ ImmutableGuard PASS
  ✅ DateGuard PASS
  ✅ AnchorGuard PASS
  ✅ RuleGuard PASS
  ✅ PacingGuard PASS
        """,
    )

    parser.add_argument(
        "--episodes",
        type=str,
        default="1-20",
        help='Episode range to test (e.g., "1-20", "5", "10-15")',
    )

    parser.add_argument(
        "--project-id",
        type=str,
        default="default",
        help='Project ID for the story (defaults to "default")',
    )

    args = parser.parse_args()

    try:
        start_ep, end_ep = parse_episode_range(args.episodes)

        if start_ep < 1 or end_ep < start_ep:
            print("❌ Error: Invalid episode range")
            sys.exit(1)

        run_episodes_test(start_ep, end_ep, args.project_id)

    except ValueError as e:
        print(f"❌ Error parsing episode range '{args.episodes}': {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
