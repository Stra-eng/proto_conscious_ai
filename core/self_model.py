from __future__ import annotations


class SelfModel:
    """
    Rich self-description for the agent.

    Holds identity attributes, value system, long-term goals, current
    focus, and a confidence level.  The `goal` and `risk_aversion`
    properties provide backward-compatible access for the Planner and
    Introspector.
    """

    def __init__(
        self,
        identity: dict | None = None,
        values: dict | None = None,
        long_term_goals: list | None = None,
        current_focus: str | None = None,
        confidence_level: float = 0.7,
    ):
        self.identity = identity or {}
        self.values = values or {}
        self.long_term_goals = long_term_goals or []
        self.current_focus = current_focus
        self.confidence_level = confidence_level  # 0..1

    # ------------------------------------------------------------------
    # Backward-compatible properties used by Planner and Introspector
    # ------------------------------------------------------------------

    @property
    def goal(self) -> str:
        """Active goal: current_focus, first long-term goal, or default."""
        if self.current_focus:
            return self.current_focus
        return self.long_term_goals[0] if self.long_term_goals else "collect_reward"

    @property
    def risk_aversion(self) -> float:
        """Risk-aversion level (0 = risk-taking, 1 = fully safe)."""
        return self.values.get("risk_aversion", 0.3)

    @risk_aversion.setter
    def risk_aversion(self, value: float) -> None:
        self.values["risk_aversion"] = round(min(max(value, 0.0), 1.0), 4)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def describe(self) -> dict:
        """Return a full snapshot of the self-model."""
        return {
            "identity":       self.identity,
            "values":         self.values,
            "long_term_goals": self.long_term_goals,
            "current_focus":  self.current_focus,
            "confidence_level": self.confidence_level,
        }

    def set_focus(self, goal: str) -> None:
        """Set the current focus and register it as a long-term goal if new."""
        self.current_focus = goal
        if goal not in self.long_term_goals:
            self.long_term_goals.append(goal)

    def add_value(self, key: str, value: float) -> None:
        """Add or update an entry in the value system."""
        self.values[key] = value

    def update_confidence(self, delta: float) -> None:
        """Nudge confidence_level by delta and clamp to [0.0, 1.0]."""
        self.confidence_level = round(min(max(self.confidence_level + delta, 0.0), 1.0), 3)

    def predict_choice_style(self) -> str:
        """Predict decision style from risk_aversion."""
        if self.risk_aversion >= 0.6:
            return "safe_preferring"
        elif self.risk_aversion <= 0.2:
            return "risk_taking"
        return "balanced"
