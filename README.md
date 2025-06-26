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

### Other Commands

```bash
# Show pipeline information
python -m src.main info

# Generate different episodes
python -m src.main run --episode 5
python -m src.main run --episode 10
```
