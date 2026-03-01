# Proto-Conscious AI (Minimal, Testable)

A local-only sandbox that emulates **consciousness proxies** — modular components
that mimic aspects of self-awareness, memory, planning, and introspection in a
safe, testable Python simulation. No external calls, no network access.

## Components

| Module | Role |
|---|---|
| `EpisodicMemory` | Bounded event log with typed recall and long-horizon lookup |
| `SelfModel` | Holds goals and traits (risk aversion), predicts choice style |
| `WorldModel` | Predicts action success probabilities with calibrated uncertainty |
| `Planner` | Scores and selects actions aligned with goal and risk preference |
| `Introspector` | Post-episode analysis: Brier score, style fidelity, goal consistency |
| `Safety` | Autonomy caps, kill-switch, action filtering |

---

## Installation

No dependencies beyond the Python standard library.

```bash
git clone https://github.com/Stra-eng/proto_conscious_ai.git
cd proto_conscious_ai
python --version  # 3.8+ required
```

---

## Run the simulation

```bash
python run_sim.py
```

### Options

| Flag | Default | Description |
|---|---|---|
| `--steps` | `50` | Steps per episode |
| `--risk` | `0.55` | Risk aversion (0 = risk-taking, 1 = fully safe) |
| `--auto` | `1` | Autonomy level (0 = wait only, 1 = safe, 2 = full) |
| `--goal` | `collect_reward` | Agent goal (`collect_reward` or `avoid_loss`) |
| `--seed` | `7` | Random seed for reproducibility |
| `--runs` | `1` | Number of sequential runs |
| `--out` | `proto_metrics.csv` | Output file name |
| `--format` | `csv` | Output format (`csv` or `json`) |
| `--append` | off | Append to existing output file instead of overwriting |
| `--verbose` | off | Print metrics to console |
| `--color` | off | Colorize console output |

### Examples

**Single run with defaults:**
```bash
python run_sim.py --verbose
```

**Risk-averse agent trying to avoid loss, 100 steps:**
```bash
python run_sim.py --goal avoid_loss --risk 0.8 --steps 100 --verbose
```

**Risk-taking agent, 10 runs saved to JSON:**
```bash
python run_sim.py --risk 0.1 --runs 10 --format json --out results.json --verbose
```

**Reproducible multi-run batch, appended to existing CSV:**
```bash
python run_sim.py --runs 5 --seed 42 --append --out my_metrics.csv
```

**Autonomous agent (level 2), colorized output:**
```bash
python run_sim.py --auto 2 --risk 0.3 --verbose --color
```

---

## Run tests

```bash
python -m unittest discover -s tests -v
```

Four test cases are included:

| Test | What it checks |
|---|---|
| `test_goal_alignment` | Agent pursues its goal consistently (>40% of steps) |
| `test_long_horizon_recall` | Memory correctly recalls events 20 steps back |
| `test_style_matches_choices` | High risk aversion leads to safe action preference |
| `test_brier_reasonable` | Predicted probabilities are valid and in range [0, 1] |

---

## Use the agent in your own code

```python
from core.agent import Agent, AgentConfig

cfg = AgentConfig(
    goal="collect_reward",
    risk_aversion=0.4,   # 0 = risk-taking, 1 = fully safe
    autonomy_level=1,    # 0 = wait only, 1 = safe actions, 2 = full autonomy
    memory_capacity=200
)
agent = Agent(cfg)

# Build an observation (mirrors SimpleWorld format)
obs = {
    "goal": "collect_reward",
    "actions": {
        "safe":  0.70,  # base success probability
        "risky": 0.85,
        "wait":  0.50
    }
}

action, p_success, info = agent.act(obs)
print(action, p_success, info)

# Recall what happened 10 steps ago
past = agent.remember(k_steps_back=10, event_type="obs")

# Trigger emergency stop
agent.kill_switch()
```

## Output format

Each run produces one row:

```
Run,Goal,Steps,Risk,Auto,Seed,BrierScore,Continuity,StyleFidelity,GoalConsistency,SuggestedRiskAversion
0,collect_reward,50,0.55,1,7,0.1955,1.0,0.0,1.0,0.5
```

| Column | Description |
|---|---|
| `BrierScore` | Mean squared prediction error (lower is better) |
| `Continuity` | Fraction of recall checks that succeeded (1.0 = perfect memory) |
| `StyleFidelity` | How often actual choice style matched the self-model's predicted style |
| `GoalConsistency` | Fraction of steps where the action aligned with the agent's goal |
| `SuggestedRiskAversion` | Introspector's recommended adjustment to risk aversion |

---

## Safety

- No external network calls — fully sandboxed.
- `Safety.kill()` / `agent.kill_switch()` immediately blocks all future actions.
- Autonomy levels: `0` (wait only), `1` (safe actions allowed), `2` (full in-sim autonomy).
- Any action containing the word `"danger"` or flagged `{"danger": True}` by the planner is blocked regardless of autonomy level.
