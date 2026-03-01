# run_sim.py
from pathlib import Path
import csv
import argparse
import json
from core.metrics import brier_score, continuity_score
from sim.simple_world import run_episode

# --- ANSI color helpers ---
class C:
    R = "\033[31m"   # red
    G = "\033[32m"   # green
    Y = "\033[33m"   # yellow
    B = "\033[34m"   # blue
    RESET = "\033[0m"

def colorize(s, col, on):
    return f"{col}{s}{C.RESET}" if on else str(s)

# --- metrics helper ---
def metrics_table(res, run_idx, goal, steps, risk, auto, seed):
    checks = [e for e in res["log"] if e["type"] == "recall_check"]
    cont = continuity_score(sum(1 for c in checks if c["ok"]), len(checks))
    brier = brier_score(res["probs"], res["outcomes"])
    style = res["report"].get("style_fidelity")
    goalc = res["report"].get("goal_consistency")
    return {
        "Run": run_idx,
        "Goal": goal,
        "Steps": steps,
        "Risk": risk,
        "Auto": auto,
        "Seed": seed,
        "BrierScore": round(brier, 4) if brier is not None else None,
        "Continuity": round(cont, 4) if cont is not None else None,
        "StyleFidelity": round(style, 4) if style is not None else None,
        "GoalConsistency": round(goalc, 4) if goalc is not None else None,
        "SuggestedRiskAversion": res["report"].get("suggest_risk_aversion")
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Proto Conscious AI Simulation")
    parser.add_argument("--steps", type=int, default=50, help="Number of steps in the simulation")
    parser.add_argument("--risk", type=float, default=0.55, help="Risk aversion level (0-1)")
    parser.add_argument("--auto", type=int, default=1, help="Autonomy level")
    parser.add_argument("--goal", type=str, default="collect_reward", help="Agent's goal")
    parser.add_argument("--seed", type=int, default=7, help="Random seed")
    parser.add_argument("--out", type=str, default="proto_metrics.csv", help="Output CSV file name")
    parser.add_argument("--runs", type=int, default=1, help="Number of simulation runs")
    parser.add_argument("--append", action="store_true", help="Append to CSV instead of overwriting")
    parser.add_argument("--verbose", action="store_true", help="Print detailed output to console")
    parser.add_argument("--format", type=str, choices=["csv", "json"], default="csv", help="Output format")
    parser.add_argument("--color", action="store_true", help="Colorize console output")

    args = parser.parse_args()

    all_tables = []
    for i in range(args.runs):
        if args.verbose:
            print(f"\n=== Running simulation {i+1} of {args.runs} ===")
        seed_i = args.seed + i
        res = run_episode(
            steps=args.steps,
            risk_aversion=args.risk,
            autonomy_level=args.auto,
            seed=seed_i,
            goal=args.goal
        )
        table = metrics_table(res, i, args.goal, args.steps, args.risk, args.auto, seed_i)
        all_tables.append(table)

        if args.verbose:
            for k, v in table.items():
                print(f"{k}: {v}")

    # Save results
    out_path = Path(args.out)
    mode = "a" if args.append and out_path.exists() else "w"

    if args.format == "csv":
        with open(out_path, mode, newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(all_tables[0].keys()))
            if mode == "w":
                w.writeheader()
            w.writerows(all_tables)
    elif args.format == "json":
        existing = []
        if args.append and out_path.exists():
            with open(out_path, "r") as f:
                existing = json.load(f)
        existing.extend(all_tables)
        with open(out_path, "w") as f:
            json.dump(existing, f, indent=2)

    if args.verbose or args.color:
        print(f"\nSaved metrics to {out_path}") 