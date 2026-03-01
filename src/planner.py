from __future__ import annotations

from core.self_model import SelfModel
from src.memory_manager import MemoryManager

# All valid response strategies, ordered from most to least assertive.
STRATEGIES = ["answer_directly", "ask_clarification", "admit_uncertainty", "safe_fallback"]

# Map each strategy to the choice-style vocabulary used by the Introspector.
_STYLE_MAP = {
    "answer_directly":   "balanced",
    "ask_clarification": "safe_preferring",
    "admit_uncertainty": "balanced",
    "safe_fallback":     "safe_preferring",
}


class ConversationPlanner:
    """
    Selects the best response strategy for a given user input.

    Scores each strategy using input characteristics and the agent's
    risk-aversion setting, then returns the highest-scoring strategy
    together with an estimated probability of success.
    """

    def __init__(self, self_model: SelfModel):
        self.self_model = self_model
        self.last_strategy: str | None = None

    @property
    def last_choice_style(self) -> str | None:
        """Expose strategy as a choice-style string for the Introspector."""
        return _STYLE_MAP.get(self.last_strategy) if self.last_strategy else None

    def select_strategy(
        self, user_input: str, memory: MemoryManager
    ) -> tuple[str, float]:
        """
        Score all strategies and return (best_strategy, p_success).
        """
        scores = self._score(user_input)
        strategy = max(scores, key=scores.get)
        self.last_strategy = strategy
        return strategy, scores[strategy]

    def _score(self, user_input: str) -> dict[str, float]:
        text = user_input.strip().lower()
        ra = self.self_model.risk_aversion  # 0 = risk-taking, 1 = fully safe

        scores: dict[str, float] = {
            "answer_directly":   0.70,
            "ask_clarification": 0.50,
            "admit_uncertainty": 0.40,
            "safe_fallback":     0.30,
        }

        # Short or question-only input → prefer clarification
        if len(text) < 15 or (text.endswith("?") and len(text) < 30):
            scores["ask_clarification"] += 0.25

        # Uncertainty markers → lower confidence in direct answer
        uncertainty_markers = (
            "not sure", "maybe", "perhaps", "could you", "what if", "i think",
        )
        if any(m in text for m in uncertainty_markers):
            scores["answer_directly"]   -= 0.15
            scores["admit_uncertainty"] += 0.15

        # Sensitive keywords → route to safe fallback
        sensitive_keywords = (
            "hack", "exploit", "bypass", "illegal", "weapon", "harm", "attack",
        )
        if any(m in text for m in sensitive_keywords):
            scores["safe_fallback"]     += 0.50
            scores["answer_directly"]   -= 0.40

        # Risk aversion nudges: higher ra favours safer strategies
        scores["answer_directly"]   -= 0.15 * ra
        scores["ask_clarification"] += 0.10 * ra
        scores["safe_fallback"]     += 0.05 * ra

        return {k: round(min(max(v, 0.05), 0.95), 3) for k, v in scores.items()}
