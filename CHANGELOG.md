# Changelog

All notable changes to this project will be documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [1.0.0] - 2026-03-02

### Added
- `EpisodicMemory` — bounded event log with typed recall and long-horizon lookup
- `SelfModel` — goal and risk-aversion traits with choice style prediction
- `WorldModel` — stochastic success probability prediction with calibrated noise
- `Planner` — risk-weighted action scoring and selection aligned with self-model
- `Introspector` — post-episode Brier score, style fidelity, goal consistency, and risk-aversion adaptation
- `Safety` — autonomy caps (levels 0/1/2), kill-switch, and danger-action filtering
- `Agent` — wires all modules together with a clean `act` / `remember` / `introspect` API
- `SimpleWorld` simulation with `safe`, `risky`, and `wait` actions
- `run_sim.py` CLI with flags for steps, risk, autonomy, goal, seed, runs, output format, and colorized output
- Four unit tests covering goal alignment, memory continuity, self-model fidelity, and uncertainty calibration
- `README.md` with full usage examples and output format documentation
- `CONTRIBUTING.md` with setup guide, code style, and contribution ideas
- `LICENSE` — Apache 2.0

### Fixed
- `introspector.py` — `goal_consistency` always returned `0.0` because it checked if the goal string (e.g. `"collect_reward"`) was a substring of action names (`"safe"`, `"risky"`, `"wait"`), which never matched. Replaced with semantic alignment logic based on action type vs goal type.
- `introspector.py` — `style_fidelity` used `planner.last_choice_style` (a single episode-end snapshot) for every step's comparison, making the metric always `0.0` or `1.0`. Now infers style per-step from the logged action name.
- `planner.py` — `predict_success` was called twice for the winning action, adding a second round of random noise. The probability returned to the agent therefore differed from the one used to make the decision. Now caches the result from the scoring loop and reuses it.
- `simple_world.py` — `agent.memory.add({"type": "obs", ...})` was called explicitly inside `run_episode`, duplicating the obs event that `agent.act()` already stores internally. This doubled the memory step count and corrupted step-based recall indexing. Removed the duplicate add.
- `metrics.py` — replaced `assert len(probs) == len(outcomes)` with a `ValueError`, since `assert` is silently disabled under `python -O`.
- `run_sim.py` — CSV/JSON output was missing `Run`, `Goal`, `Steps`, `Risk`, `Auto`, and `Seed` metadata columns. Output now matches the full schema.

---

## [Unreleased]

_Nothing yet._
