# AGENTS.md

## Cursor Cloud specific instructions

### Overview

Proto-Conscious AI is a pure Python sandbox with four distinct agent layers, each building on the previous:

| Layer | Entry point | Dependencies | API keys needed |
|---|---|---|---|
| **Simulation agent** | `run_sim.py` | stdlib only | None |
| **Core library** | `core/agent.py` | stdlib only (except `core/memory_graph.py`) | None |
| **Anthropic assistant** | `main.py` → `src/agent_core.py` | `anthropic` | `ANTHROPIC_API_KEY` |
| **Cognitive agent** | `src/cognitive_agent.py` | `openai`, `tiktoken` | `OPENAI_API_KEY` |
| **ProtoAI v3** | `src/proto_ai_v3.py` | `openai`, `tiktoken`, `sentence-transformers`, `numpy`, `networkx` | `OPENAI_API_KEY` |

### Architecture

**`core/`** — Pure stdlib modules (zero pip deps). Each has a single responsibility:
- `agent.py` — Wires all core modules via `Agent` + `AgentConfig`
- `memory.py` — `EpisodicMemory`: bounded event log with typed recall
- `self_model.py` — `SelfModel`: goals, traits (risk aversion), style prediction
- `world_model.py` — `WorldModel`: success probability prediction with calibrated uncertainty
- `planner.py` — `Planner`: risk-weighted action scoring and selection
- `introspector.py` — `Introspector`: post-episode Brier score, style fidelity, goal consistency
- `safety.py` — `Safety`: autonomy caps, kill-switch, danger-word filtering
- `metrics.py` — `brier_score()`, `continuity_score()`
- `reflector.py` — Per-response alignment/uncertainty/conflict detection
- `simulator.py` — Outcome simulation functions
- `memory_graph.py` — **Exception**: requires numpy, networkx, sentence-transformers. Graph-based memory with embeddings. Only imported by `src/proto_ai_v3.py`.

**`sim/`** — `simple_world.py` provides `SimpleWorld` environment + `run_episode()` for simulation runs.

**`src/`** — LLM-integrated layers:
- `agent_core.py` — `AgentCore` orchestrator: wires memory manager, reasoning engine, planner, reflector, introspector. Uses Anthropic Claude API.
- `reasoning_engine.py` — Anthropic API wrapper for `AgentCore`.
- `memory_manager.py` — Conversation history + JSON persistence for `AgentCore`.
- `planner.py` — `ConversationPlanner`: strategy selection (answer/clarify/fallback) for `AgentCore`.
- `cognitive_agent.py` — OpenAI-based structured reasoning with tool use, hierarchical planning, and self-improvement loop. Independent from `AgentCore`.
- `proto_ai_v3.py` — Full cognitive pipeline combining `cognitive_agent.py` components with `core/memory_graph.py` for graph-based memory. Imports `cognitive_agent` as a sibling (not `src.cognitive_agent`), so must be run from `src/` or with `src/` on `PYTHONPATH`.

### Running tests and simulation

- **Tests:** `python3 -m unittest discover -s tests -v` (stdlib only, no API keys)
- **Simulation:** `python3 run_sim.py --verbose` (stdlib only, no API keys)
- **Lint:** `ruff check .` (requires `~/.local/bin` on PATH)
- See `README.md` for full CLI flags and examples.

### Testing patterns

- All tests live in `tests/` and use `unittest.TestCase`.
- Tests are stdlib-only — they test the `core/` + `sim/` layers, never the `src/` LLM layers.
- Test naming convention: `test_<module>.py` with descriptive method names.
- When adding a new `core/` module, add a corresponding `tests/test_<module>.py`.
- The CI workflow (`.github/workflows/ci.yml`) runs tests on Python 3.8, 3.10, 3.12 and a smoke-test simulation (`--steps 20 --runs 2`). It does **not** install `requirements.txt`.

### Code conventions

- `core/` and `sim/` must remain stdlib-only (no pip deps). This is intentional — see `CONTRIBUTING.md`.
- `core/memory_graph.py` is the sole exception; it's isolated behind a try/except import in `cognitive_agent.py`.
- No type-checking tool is configured; type hints are used informally.
- No formatter is configured; follow existing code style (PEP 8-ish).

### Important caveats

- `pip install` writes to `~/.local/` (user install). Add `~/.local/bin` to PATH: `export PATH="$HOME/.local/bin:$PATH"`.
- `src/proto_ai_v3.py` imports `cognitive_agent` as a bare module name (not `src.cognitive_agent`). To run it standalone, either `cd src/` first or set `PYTHONPATH=src`.
- `sentence-transformers` auto-downloads the `all-MiniLM-L6-v2` model (~80 MB) on first use. Requires internet.
- No Docker, no database, no background services needed.
- Generated output files (`proto_metrics.csv`, `*.json`, `agent_memories.jsonl`) are created in the working directory; clean up after test runs if needed.
- The `main.py` REPL reads from stdin — it cannot be tested non-interactively without piping input (e.g., `echo "hello\nexit" | python3 main.py`).
