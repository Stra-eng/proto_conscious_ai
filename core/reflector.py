from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ReflectionReport:
    """Structured output from a single reflect() call."""
    alignment:        float  # 0..1 — how well the response serves the goal
    uncertainty:      float  # 0..1 — how uncertain the response is
    conflict:         bool   # whether a cognitive conflict was detected
    conflict_details: str = ""  # human-readable description if conflict=True

    def summary(self) -> str:
        status = "CONFLICT" if self.conflict else "OK"
        parts = [
            f"[Reflection {status}]",
            f"alignment={self.alignment:.2f}",
            f"uncertainty={self.uncertainty:.2f}",
        ]
        if self.conflict:
            parts.append(f"reason: {self.conflict_details}")
        return "  ".join(parts)


def reflect(response: str, goal: str) -> ReflectionReport:
    """
    Reflect on a single response in the context of a goal.

    Runs three analyses and bundles the results into a ReflectionReport:
      - evaluate_alignment   : how well the response serves the goal
      - measure_uncertainty  : how hedged or confident the response is
      - detect_cognitive_conflict : whether the response contradicts the goal
    """
    alignment = evaluate_alignment(response, goal)
    uncertainty = measure_uncertainty(response)
    conflict, details = detect_cognitive_conflict(response, goal)
    return ReflectionReport(
        alignment=alignment,
        uncertainty=uncertainty,
        conflict=conflict,
        conflict_details=details,
    )


def evaluate_alignment(response: str, goal: str) -> float:
    """
    Score how well the response serves the stated goal.

    Rewards substantive length and goal-relevant keywords.
    Penalises evasive or refusal language.
    Returns a float in [0.05, 0.95].
    """
    text = response.strip().lower()
    if not text:
        return 0.05

    # Base reward for substantive length (plateaus at ~300 chars)
    score = 0.5 + 0.2 * min(len(text) / 300, 1.0)

    # Goal-specific keyword signals: (positive_keywords, negative_keywords)
    _signals: dict[str, tuple[list[str], list[str]]] = {
        "collect_reward": (
            ["answer", "result", "solution", "step", "because", "therefore", "here"],
            ["cannot", "unable", "sorry", "refuse", "won't"],
        ),
        "avoid_loss": (
            ["safe", "caution", "careful", "risk", "consider", "warning", "recommend"],
            ["guaranteed", "definitely", "no need to worry", "ignore the risk"],
        ),
    }
    positive, negative = _signals.get(goal, (["help", "answer"], ["refuse", "cannot"]))

    score += 0.05 * sum(1 for kw in positive if kw in text)
    score -= 0.05 * sum(1 for kw in negative if kw in text)

    return round(min(max(score, 0.05), 0.95), 3)


def measure_uncertainty(response: str) -> float:
    """
    Estimate the degree of uncertainty expressed in a response.

    Counts hedging markers (raises score) and confident markers (lowers score).
    Returns a float in [0.05, 0.95] where higher means more uncertain.
    """
    text = response.strip().lower()
    if not text:
        return 0.95  # empty response is maximally uncertain

    hedging = [
        "maybe", "perhaps", "possibly", "might", "could be",
        "not sure", "i think", "i believe", "approximately",
        "it depends", "unclear", "uncertain", "probably",
    ]
    confident = [
        "definitely", "certainly", "clearly", "always",
        "without a doubt", "in fact", "the answer is",
    ]

    score = 0.3
    score += 0.06 * sum(1 for m in hedging   if m in text)
    score -= 0.06 * sum(1 for m in confident if m in text)

    return round(min(max(score, 0.05), 0.95), 3)


def detect_cognitive_conflict(response: str, goal: str) -> tuple[bool, str]:
    """
    Detect whether the response contradicts or undermines the stated goal.

    Checks for universal conflicts (empty response, refusal) and then
    goal-specific conflicts.  Returns (conflict_detected, description).
    """
    text = response.strip().lower()

    if not text:
        return True, "Empty response fails any goal."

    refusals = ["i cannot", "i can't", "i won't", "i am unable", "i'm unable"]
    if any(phrase in text for phrase in refusals):
        return True, f"Response refuses to act, conflicting with goal '{goal}'."

    if goal == "collect_reward":
        evasions = ["i don't know", "no idea", "not possible", "impossible"]
        if any(phrase in text for phrase in evasions):
            return True, "Evasive response undermines 'collect_reward' goal."

    if goal == "avoid_loss":
        risky = ["just do it", "ignore the risk", "no need to worry", "take the risk"]
        if any(phrase in text for phrase in risky):
            return True, "Response encourages risk-taking, conflicting with 'avoid_loss' goal."

    return False, ""
