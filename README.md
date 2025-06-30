# Final_engine
my-novel-engine

## Quick Demo

Generate your first episode with the integrated pipeline:

```bash
# Generate for default project
python -m src.main run --episode 1
cat projects/default/outputs/episode_1.txt

# Generate for a specific project
python -m src.main run --episode 1 --project-id demo_novel
cat projects/demo_novel/outputs/episode_1.txt
```

### Platform Style Configuration

The engine supports different writing styles for different platforms. Configure the style by setting the `PLATFORM` environment variable:

```bash
# Use munpia style (default)
PLATFORM=munpia python -m src.main run --episode 1

# Use kakao style  
PLATFORM=kakao python -m src.main run --episode 1
```

Available platforms:
- **munpia**: 대사 중심 경쾌한 스타일 (dialogue-focused, upbeat style)
- **kakao**: 정서적 깊이감 있는 스타일 (emotionally deep style)

You can also set this in your `.env` file:
```
PLATFORM=munpia
```

## Advanced Settings

### LLM Temperature Control

The engine allows fine-tuning of creativity levels for different pipeline stages using temperature parameters:

```bash
# Experimental draft with higher creativity
export TEMP_DRAFT=0.85
python scripts/run_pipeline.py --project-id easy-money --episodes 1-1
```

Available temperature settings:
- **TEMP_DRAFT**: Controls creativity for final draft generation (default: 0.7)
- **TEMP_BEAT**: Controls creativity for beat planning (default: 0.3)  
- **TEMP_SCENE**: Controls creativity for scene generation (default: 0.6)

You can set these in your `.env` file:
```env
TEMP_DRAFT=0.7
TEMP_BEAT=0.3
TEMP_SCENE=0.6
```

The log output will show the temperature being used:
```
✍️  Draft Generator… (temperature=0.85, max_output_tokens=60000)
```

This will run the complete pipeline:
1. **Arc Outliner** → Creates basic story arc structure
2. **Beat Planner v2** → Generates 3-Act structure with 6 sequences and 4 beats each
3. **Scene Maker v2** → Creates 8-12 ScenePoints from the beats with enhanced metadata
4. **Context Builder** → Combines scenes into narrative context
5. **Draft Generator** → Produces final episode draft

### Scene Maker v2 Structure

Scene Maker v2 now generates 8-12 detailed ScenePoints per beat with enhanced metadata:

**ScenePoint Schema:**
```yaml
scene_03:
  pov: side          # main | side
  purpose: "훈련 결과 발표"
  tags: ["지아", "교관", "훈련장"]
  desc: "지아는 낮은 점수에도 불구하고 교관의 시선을 느낀다…"
```

**Key Features:**
- **pov**: Perspective type (`main` for main character, `side` for supporting character)
- **purpose**: Brief narrative purpose of the scene (Korean, 10-30 characters)
- **tags**: List of characters and locations mentioned in the scene
- **desc**: Detailed scene description (Korean, 50-150 characters)

The Scene Maker v2 also stores scene metadata in the vector database for enhanced search and retrieval capabilities.

### Beat Planner v2 Structure

The Beat Planner now generates beats in a structured 3-Act format:

**3-Act Structure:**
- **Act 1 (Setup)**: Sequences 1-2 
- **Act 2 (Confrontation)**: Sequences 3-4
- **Act 3 (Resolution)**: Sequences 5-6

**Each sequence contains 4 beats:**
- `beat_1`, `beat_2`, `beat_3`: Story progression beats
- `beat_tp`: Turning point for narrative tension

**Output Example:**
```yaml
ep_42:
  seq_2:
    beat_1: "훈련에서 굴욕적인 패배"
    beat_2: "비밀 연습 시작"
    beat_3: "첫 가시적 성장"
    beat_tp: "교관의 의심 어린 시선"
```

This structure is fully compatible with Scene Maker v2 and uses the `seq_x/beat_y` format for seamless integration.

### Guard Configuration

The engine supports advanced quality control through configurable guards. Set thresholds in your `.env` file:

```bash
# Self-Critique Guard: LLM-based fun & logic evaluation
MIN_CRITIQUE_SCORE=7.0    # Minimum score (1-10) for fun and logic

# Other guard settings (examples)
# LEXI_TTR_THRESHOLD=0.17
# EMOTION_DELTA_MAX=0.7
```

**Self-Critique Guard Features:**
- Uses Gemini 2.5 Pro to evaluate generated content
- Scores content on two dimensions: **재미 (fun)** and **개연성 (logic)**
- Raises RetryException if `min(fun, logic) < MIN_CRITIQUE_SCORE`
- Integrated into Beat Planner, Scene Maker, and Draft Generator workflows
- Automatic retry with exponential backoff on low scores

Test with different thresholds:
```bash
# Strict quality control
MIN_CRITIQUE_SCORE=8.5 python scripts/run_pipeline.py --episode 2

# Relaxed quality control  
MIN_CRITIQUE_SCORE=6.0 python scripts/run_pipeline.py --episode 2
```

The output is saved to `projects/{project-id}/outputs/episode_1.txt` with placeholder content that will be replaced by actual LLM-generated text in future versions.

## Guard Chain Testing

Test the complete guard validation system with the pipeline smoke test:

```bash
# Test default project
python scripts/run_pipeline.py --episodes 1-20

# Test specific project
python scripts/run_pipeline.py --project-id demo_novel --episodes 1-3
```

This runs all guards in sequence for each episode:
- **LexiGuard** → Checks lexical quality (TTR, 3-gram duplication)
- **EmotionGuard** → Monitors emotional transitions
- **ScheduleGuard** → Validates foreshadow resolution compliance  
- **ImmutableGuard** → Ensures character consistency
- **DateGuard** → Checks chronological progression
- **AnchorGuard** → Validates anchor event compliance
- **RuleGuard** → Checks forbidden pattern violations
- **RelationGuard** → Monitors character relationship changes
- **PacingGuard** → Validates narrative pacing balance
- **CritiqueGuard** → LLM-based fun & logic evaluation

Expected output format:
```
✅ LexiGuard PASS
✅ EmotionGuard PASS
✅ ScheduleGuard PASS
✅ ImmutableGuard PASS
✅ DateGuard PASS
✅ AnchorGuard PASS
✅ RuleGuard PASS
✅ RelationGuard PASS
✅ PacingGuard PASS
✅ CritiqueGuard PASS
```

## 통합 테스트 실행 예시

Test anchor-driven integration flow to ensure all 5 anchor events appear within their expected episodes:

```bash
# Test default project
python scripts/run_anchor_flow.py

# Test specific project  
python scripts/run_anchor_flow.py --project-id demo_novel
```

This validates that all anchor events from `projects/{project-id}/data/anchors.json` appear within their target episodes (anchor_ep ± 1) across a 20-episode simulation:

- **ANCHOR_01**: 주인공 첫 등장 (Episode 1)
- **ANCHOR_02**: 첫 번째 시련 (Episode 5) 
- **ANCHOR_03**: 중요한 만남 (Episode 10)
- **ANCHOR_04**: 결정적 선택 (Episode 15)
- **ANCHOR_05**: 마지막 대결 (Episode 20)

Expected output:
```
🎯 TEST RESULT: PASS
   All anchor events were found in their expected episodes!
🎉 SUCCESS: All anchor events validated!
```

Exit codes:
- **0**: All 5 anchors found in correct episodes
- **1**: One or more anchors missing + failure log

### Other Commands

```bash
# Show pipeline information
python -m src.main info

# Generate different episodes for different projects
python -m src.main run --episode 5 --project-id default
python -m src.main run --episode 10 --project-id demo_novel

# Test guard chain with pipeline smoke test
python scripts/run_pipeline.py --project-id default --episodes 1-20
python scripts/run_pipeline.py --project-id demo_novel --episodes 5      # Single episode
python scripts/run_pipeline.py --project-id default --episodes 10-15     # Episode range
```
