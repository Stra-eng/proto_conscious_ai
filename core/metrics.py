
def brier_score(probs, outcomes):
    if len(probs) != len(outcomes):
        raise ValueError(f"probs and outcomes must have the same length ({len(probs)} vs {len(outcomes)})")
    return sum((p - y)**2 for p,y in zip(probs, outcomes)) / len(probs) if probs else None

def continuity_score(recalled_ok, total_checks):
    return recalled_ok / total_checks if total_checks else None
