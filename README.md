
# Proto-Conscious AI (Minimal, Testable)

This project emulates **consciousness proxies** in a safe, local-only sandbox:

- **Memory** (persistent episodic log, long-horizon recall)
- **SelfModel** (goals/traits, predicts choice style)
- **WorldModel** (predicts success prob., uncertainty)
- **Planner** (chooses actions consistent with self/goal)
- **Introspector** (post-episode metrics & adaptation)
- **Safety** (autonomy caps, kill-switch, action filter)

## Run simulation
```bash
python run_sim.py
```
Outputs metrics and `/mnt/data/proto_metrics.csv`.

## Run tests
```bash
python -m unittest discover -s tests -v
```

## Safety
- No external calls. 
- `Safety.kill()` immediately blocks actions.
- Autonomy levels: 0 (no actions, wait only), 1 (safe), 2 (full in-sim autonomy).
