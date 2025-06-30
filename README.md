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

This will run the complete pipeline:
1. **Arc Outliner** → Creates basic story arc structure
2. **Beat Planner** → Generates 3 story beats 
3. **Scene Maker** → Creates ~10 scenes from the beats
4. **Context Builder** → Combines scenes into narrative context
5. **Draft Generator** → Produces final episode draft

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

Expected output format:
```
✅ LexiGuard PASS
✅ EmotionGuard PASS
✅ ScheduleGuard PASS
✅ ImmutableGuard PASS
✅ DateGuard PASS
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
