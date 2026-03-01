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

## [1.2.0] - 2026-03-02

### Added
- `src/memory_manager.py` — `MemoryManager` wraps `EpisodicMemory` with conversation turn history in LLM messages format and JSON session persistence (`save` / `load`)
- `src/reasoning_engine.py` — `ReasoningEngine` wraps the Anthropic API with a heuristic confidence scorer; raises `RuntimeError` at construction if `ANTHROPIC_API_KEY` is missing
- `src/planner.py` — `ConversationPlanner` scores four response strategies (`answer_directly`, `ask_clarification`, `admit_uncertainty`, `safe_fallback`) using input heuristics and risk-aversion; exposes `last_choice_style` for the `Introspector`
- `src/agent_core.py` — `AgentCore` orchestrates all modules behind a single `respond()` method; runs introspection every 5 turns and adapts `risk_aversion`; supports `save_session` / `resume_session`
- `main.py` — interactive REPL entry point with `save <path>` command and clean exit handling
- `requirements.txt` — `anthropic>=0.40.0` (only external dependency)
- `SYSTEM_PROMPT.md` — system prompt for using the project as an AI assistant backend

---

## [1.1.0] - 2026-03-02

### Added
- GitHub Actions CI workflow — runs unit tests and a simulation smoke test on Python 3.8, 3.10, and 3.12 on every push and pull request to `main`

---
