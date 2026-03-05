# AGENTS.md

## Cursor Cloud specific instructions

### Overview

Proto-Conscious AI is a pure Python sandbox that simulates consciousness proxies (memory, planning, introspection, safety). The core simulation (`run_sim.py`) and tests use only the Python standard library — no pip dependencies required. The `src/` directory contains LLM-integrated modules that need API keys and `requirements.txt` packages.

### Running tests and simulation

- **Tests:** `python3 -m unittest discover -s tests -v` (stdlib only, no API keys)
- **Simulation:** `python3 run_sim.py --verbose` (stdlib only, no API keys)
- **Lint:** `ruff check .` (requires `~/.local/bin` on PATH)
- See `README.md` for full CLI flags and examples.

### Important caveats

- `pip install` writes to `~/.local/` (user install). The `~/.local/bin` directory must be on PATH for tools like `ruff` to work: `export PATH="$HOME/.local/bin:$PATH"`.
- The `src/` LLM modules (`main.py`, `cognitive_agent.py`, `proto_ai_v3.py`) require `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` environment variables. The simulation and tests do not.
- `core/memory_graph.py` is the only `core/` file with external dependencies (numpy, networkx, sentence-transformers). It's imported only by `src/proto_ai_v3.py`.
- No Docker, no database, no background services needed.
- Generated output files (`proto_metrics.csv`, `*.json`) are created in the working directory; clean up after test runs if needed.
