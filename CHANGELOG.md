# Changelog

All notable changes to this project will be documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [1.9.0] - 2026-03-02

### Added
- `src/proto_ai_v3.py` — end-to-end cognitive stack orchestrator with eight-stage pipeline:
  - `SelfModel` — mood-aware agent state tracker updated before and after each turn
  - `ConfidenceCalibrator` — heuristic scorer based on epistemic token presence and response length
  - `OutcomeSimulator` — LLM-backed 3-sentence consequence forecast for draft answers
  - `ProtoAI` — orchestrates perception → memory retrieval → structured reasoning → confidence calibration → outcome simulation → reflection → memory consolidation → self-model update behind a single `respond()` call

### Fixed
- `src/proto_ai_v3.py` — `from cognitive_agent_core import` used a non-existent module name; corrected to `from cognitive_agent import`
- `src/proto_ai_v3.py` — `from memory_continuity_graph import` used a non-existent module name; corrected to `from core.memory_graph import`
- `src/proto_ai_v3.py` — `Planner` does not exist in `cognitive_agent.py`; corrected to `CognitivePlanner` (imported as `Planner` alias)
- `src/proto_ai_v3.py` — `ReasoningEngine` does not exist in `cognitive_agent.py`; corrected to `CognitiveReasoningEngine` (imported as `ReasoningEngine` alias)
- `src/proto_ai_v3.py` — `ImprovementLoop` was imported and assigned to `self.loop` but never called anywhere in `respond()`; removed dead instantiation and import
- `src/proto_ai_v3.py` — dangling empty string literal `"consequences might ensue.""` (double closing quote) in `OutcomeSimulator.simulate`; corrected to `"consequences might ensue."`

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

## [1.8.0] - 2026-03-02

### Added
- `src/cognitive_agent.py` — modular cognitive agent core with six components:
  - `ModelAdapter` — OpenAI chat completions wrapper with token counting via `tiktoken`
  - `ToolRegistry` — dynamic tool registration and invocation; descriptions stored separately from function `__doc__` to avoid mutation side effects
  - `CognitiveReasoningEngine` — chain-of-thought prompt builder that returns structured JSON (`thought` or `tool_call`)
  - `CognitivePlanner` — hierarchical task decomposition via LLM; `next_open_task()` traverses the task tree depth-first
  - `ImprovementLoop` — self-reflection loop: decomposes objectives, dispatches tool calls or generates + critiques answers, stores results in memory
  - `DataRetentionStore` — JSONL-backed fallback memory store with the same `add_memory()` interface as `MemoryContinuityGraph`
- Updated `requirements.txt`: `openai>=1.0.0`, `tiktoken>=0.7.0`

### Fixed
- Wrong import path `memory_continuity_graph` → `core.memory_graph`
- `FileRetentionStore.add()` used `write_text(..., append=True)` which is not a valid parameter — silently overwrote the file; replaced with `open(..., "a")`
- `Task.is_done()` required `self.status == "done"` even for parent tasks whose status is never set in `execute()`, causing an infinite loop once all subtasks completed; fixed so tasks with subtasks delegate to their children
- `assert task` in `execute()` replaced with `raise RuntimeError` — asserts are disabled under `python -O`
- Class `FileRetentionStore` renamed to `DataRetentionStore` to match component 6 in the module docstring
- `execute()` called `add_memory()` but `FileRetentionStore` only had `add()` — API mismatch at runtime; `DataRetentionStore` now exposes `add_memory()`; a `_store()` helper handles both interfaces safely

---

## [1.7.0] - 2026-03-02

### Added
- `core/memory_graph.py` — `MemoryContinuityGraph`, a graph-based cognitive memory substrate that replaces a plain vector database:
  - Memories are stored as `MemoryNode` objects (content, embedding, timestamp, importance) in a weighted `DiGraph`
  - New memories are auto-linked to the most similar existing nodes via cosine similarity edges
  - Edge weights decay exponentially with a one-week half-life; negligible edges are pruned
  - Retrieval ranks by cognitive salience: semantic similarity + importance + recency decay + graph connectivity strength
  - `save()` / `load()` for GraphML persistence with hex-encoded embeddings
- Updated `requirements.txt` with `sentence-transformers>=3.0.0`, `numpy>=1.24.0`, `networkx>=3.0`

### Fixed
- `save()` — original implementation mutated live graph node data, omitted `content` / `timestamp` / `importance` from the serialized graph, and left an un-serializable `obj` attribute causing `write_graphml` to fail. Fixed by building a clean serializable copy of the graph before writing.
- `load()` — `np.frombuffer()` returns a read-only view; added `.copy()` to make restored embeddings writable. Edge `weight` and `created` attributes are now also restored.

---

## [1.6.0] - 2026-03-02

### Added
- `core/simulator.py` — three simulation functions with a shared `SimContext` dataclass:
  - `simulate_outcome(action, context)` — resolves a success/failure result using `WorldModel` at sim level or response-quality heuristics at agent level; returns a `SimOutcome` dataclass with `p_success`, `risk_score`, `failure_prob`, and `summary()`
  - `score_risk(action, context)` — scores riskiness from action-name signals, inverse p_success, response content keywords, and risk-aversion scaling
  - `predict_failure(action, context)` — combines base failure probability, risk penalty, and response quality penalty
- `SimContext.from_observation()` — factory for sim-level construction from a `SimpleWorld` observation dict
- `SimContext.from_self_model()` — factory for agent-level construction from a response and `SelfModel` instance

### Fixed
- `predict_failure` — removed `if context.response:` guard on quality penalty; empty responses were producing falsely low failure probabilities since the penalty was skipped entirely. `_response_quality` returns `0.0` for empty input, giving maximum penalty correctly.

---

## [1.5.0] - 2026-03-02

### Changed
- `AgentCore.respond()` now runs `reflect(response, goal)` after every LLM response:
  - If a cognitive conflict is detected and the strategy is not already `safe_fallback`, the response is regenerated using `safe_fallback` and re-reflected
  - `self_model.confidence_level` is nudged after each turn using the alignment and uncertainty scores from the report
  - Episode log entries now include a `reflection` summary string and use `alignment` (not engine score) as the outcome signal
  - `last_reflection` exposed as a public attribute for callers to inspect the most recent `ReflectionReport`

---

## [1.4.0] - 2026-03-02

### Added
- `core/reflector.py` — `reflect(response, goal)` returns a `ReflectionReport` dataclass with three analyses:
  - `evaluate_alignment` — scores response relevance using length heuristics and goal-specific keyword signals
  - `measure_uncertainty` — counts hedging markers vs confident markers to estimate expressed uncertainty
  - `detect_cognitive_conflict` — flags refusals, empty responses, evasion (`collect_reward`), and risk-encouraging language (`avoid_loss`)
- `ReflectionReport` — typed dataclass with `alignment`, `uncertainty`, `conflict`, `conflict_details`, and a `summary()` method

---

## [1.3.0] - 2026-03-02

### Changed
- `SelfModel` replaced with a richer identity-aware implementation. New fields: `identity` (dict), `values` (dict), `long_term_goals` (list), `current_focus` (str), `confidence_level` (float). New methods: `set_focus()`, `add_value()`, `update_confidence()`. `goal` and `risk_aversion` are now backward-compatible properties — `Planner`, `Introspector`, and `run_sim.py` required no changes.

### Fixed
- Updated `SelfModel` constructor call sites in `core/agent.py`, `src/agent_core.py`, and `tests/test_selfmodel.py` to use the new signature.

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
