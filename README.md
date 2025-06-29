# Final_engine
my-novel-engine

## Quick Demo

Generate your first episode with the integrated pipeline:

```bash
python -m src.main run --episode 1
cat output/episode_1.txt
```

This will run the complete pipeline:
1. **Arc Outliner** → Creates basic story arc structure
2. **Beat Planner** → Generates 3 story beats 
3. **Scene Maker** → Creates ~10 scenes from the beats
4. **Context Builder** → Combines scenes into narrative context
5. **Draft Generator** → Produces final episode draft

The output is saved to `output/episode_1.txt` with placeholder content that will be replaced by actual LLM-generated text in future versions.

## Guard Chain Testing

Test the complete guard validation system with the pipeline smoke test:

```bash
python scripts/run_pipeline.py --episodes 1-20
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
python scripts/run_anchor_flow.py
```

This validates that all anchor events from `data/anchors.json` appear within their target episodes (anchor_ep ± 1) across a 20-episode simulation:

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

# Generate different episodes
python -m src.main run --episode 5
python -m src.main run --episode 10

# Test guard chain with pipeline smoke test
python scripts/run_pipeline.py --episodes 1-20
python scripts/run_pipeline.py --episodes 5      # Single episode
python scripts/run_pipeline.py --episodes 10-15  # Episode range
```
