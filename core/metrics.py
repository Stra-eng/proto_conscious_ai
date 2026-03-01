
def brier_score(probs, outcomes):
    assert len(probs) == len(outcomes)
    return sum((p - y)**2 for p,y in zip(probs, outcomes)) / len(probs) if probs else None

def continuity_score(recalled_ok, total_checks):
    return recalled_ok / total_checks if total_checks else None
