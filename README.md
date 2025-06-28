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
