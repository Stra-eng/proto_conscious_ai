# Contributing to Proto-Conscious AI

Thanks for your interest in contributing! This document covers how to get set up, the project conventions, and how to submit changes.

---

## Getting started

1. **Fork** the repo on GitHub and clone your fork:
   ```bash
   git clone https://github.com/your-username/proto_conscious_ai.git
   cd proto_conscious_ai
   ```

2. **Create a branch** for your change:
   ```bash
   git checkout -b feat/your-feature-name
   ```

3. **Make your changes**, then run the tests to make sure nothing is broken:
   ```bash
   python -m unittest discover -s tests -v
   ```

4. **Run the simulation** to verify end-to-end behaviour:
   ```bash
   python run_sim.py --verbose
   ```

5. **Commit and push**, then open a pull request against `main`.

---

## Project structure

```
proto_conscious_ai/
├── core/
│   ├── agent.py          # Wires all modules together
│   ├── memory.py         # EpisodicMemory
│   ├── self_model.py     # SelfModel (goals, traits)
│   ├── world_model.py    # WorldModel (success probabilities)
│   ├── planner.py        # Planner (action selection)
│   ├── introspector.py   # Introspector (post-episode metrics)
│   ├── safety.py         # Safety (kill-switch, autonomy caps)
│   └── metrics.py        # brier_score, continuity_score
├── sim/
│   └── simple_world.py   # SimpleWorld + run_episode()
├── tests/
│   ├── test_goal.py
│   ├── test_memory.py
│   ├── test_selfmodel.py
│   └── test_uncertainty.py
├── run_sim.py            # CLI entry point
└── README.md
```

---

## Guidelines

### Code style
- Follow existing code style — plain Python, no external dependencies.
- Keep modules small and focused on a single responsibility.
- Avoid adding third-party packages; the project is intentionally dependency-free.

### Tests
- Every new feature or bug fix should include a test in `tests/`.
- Test files follow the pattern `test_<module>.py` using `unittest.TestCase`.
- All tests must pass before submitting a PR.

### Safety
- This project is a local-only sandbox. Do not add any external network calls, file system writes outside the project directory, or system-level operations.
- Any new action types added to the simulation must be filterable by the `Safety` module.

### Commits
- Use clear, descriptive commit messages in the imperative mood:
  - `Add long-term memory decay mechanism`
  - `Fix Brier score calculation for empty episodes`
  - Not: `fixed stuff` or `update`
- One logical change per commit.

---

## What to contribute

Good areas to contribute:

- **New goals** — extend beyond `collect_reward` / `avoid_loss`
- **New action types** — richer action spaces for the simulation
- **Better world models** — e.g. multi-step predictions, correlated outcomes
- **Additional metrics** — e.g. regret, calibration curves
- **New tests** — especially edge cases (empty episodes, kill-switch mid-run, autonomy level 0)
- **Bug fixes** — check open issues on GitHub

---

## Reporting bugs

Open an issue on GitHub with:
1. What you expected to happen
2. What actually happened
3. Steps to reproduce (include `--seed` value if it's simulation-related)

---

## License

By contributing, you agree that your contributions will be licensed under the [Apache 2.0 License](LICENSE).
