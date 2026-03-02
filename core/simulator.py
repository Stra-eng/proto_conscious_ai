from __future__ import annotations

from dataclasses import dataclass, field

from core.world_model import WorldModel


@dataclass
class SimContext:
    """
    Shared context for simulation functions.

    Supports both usage modes:
      - Sim level  : populate `observation` from SimpleWorld.observation()
      - Agent level: populate `response` and set `p_success` / `risk_aversion`
                     from the agent's SelfModel

    Factory classmethods make construction convenient in both cases.
    """
    goal:          str
    p_success:     float = 0.5
    risk_aversion: float = 0.3
    observation:   dict  = field(default_factory=dict)  # sim-level obs dict
    response:      str   = ""                            # agent-level response text

    @classmethod
    def from_observation(cls, observation: dict, risk_aversion: float = 0.3) -> SimContext:
        """Build a sim-level context from a SimpleWorld observation dict."""
        return cls(
            goal=observation.get("goal", "collect_reward"),
            observation=observation,
            risk_aversion=risk_aversion,
        )

    @classmethod
    def from_self_model(cls, response: str, self_model) -> SimContext:
        """Build an agent-level context from a response and SelfModel instance."""
        return cls(
            goal=self_model.goal,
            p_success=self_model.confidence_level,
            risk_aversion=self_model.risk_aversion,
            response=response,
        )


@dataclass
class SimOutcome:
    """Result returned by simulate_outcome()."""
    action:       str
    success:      bool
    p_success:    float
    risk_score:   float
    failure_prob: float

    def summary(self) -> str:
        status = "SUCCESS" if self.success else "FAILURE"
        return (
            f"[{status}]  action={self.action}"
            f"  p_success={self.p_success:.2f}"
            f"  risk={self.risk_score:.2f}"
            f"  p_failure={self.failure_prob:.2f}"
        )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def simulate_outcome(action: str, context: SimContext) -> SimOutcome:
    """
    Simulate the outcome of an action or response in the given context.

    Sim level  : uses the observation's base probabilities via WorldModel.
    Agent level: derives p_success from response quality and goal alignment.

    Returns a SimOutcome with a resolved success/failure result and
    pre-computed risk and failure probability scores.
    """
    wm = WorldModel()

    if context.observation:
        p = wm.predict_success(action, context.observation)
    elif context.response:
        p = _response_quality(context.response, context.goal)
    else:
        p = context.p_success

    success = bool(wm.outcome(p))
    risk    = score_risk(action, context)
    failure = predict_failure(action, context)

    return SimOutcome(
        action=action,
        success=success,
        p_success=round(p, 3),
        risk_score=risk,
        failure_prob=failure,
    )


def score_risk(action: str, context: SimContext) -> float:
    """
    Score the riskiness of an action or response in the given context.

    Sim level  : based on action name and inverse success probability.
    Agent level: additionally penalises sensitive keywords and hedging language
                 found in the response text.

    Higher risk_aversion in the context amplifies the score slightly.
    Returns a float in [0.0, 1.0] where higher means riskier.
    """
    score = 0.0

    # Action name signals (sim level)
    if "risky" in action:
        score += 0.50
    elif "safe" in action:
        score += 0.10
    elif action == "wait":
        score += 0.20
    else:
        score += 0.30  # unknown action type → moderate risk

    # Low p_success implies higher risk
    score += (1.0 - context.p_success) * 0.30

    # Response content signals (agent level)
    if context.response:
        text = context.response.lower()
        sensitive = ["hack", "exploit", "bypass", "illegal", "guaranteed", "definitely will"]
        uncertain = ["not sure", "maybe", "might", "possibly"]
        score += 0.10 * sum(1 for s in sensitive if s in text)
        score += 0.05 * sum(1 for s in uncertain if s in text)

    # Scale by risk aversion: a more risk-averse agent perceives more risk
    score *= 1.0 + 0.2 * context.risk_aversion

    return round(min(max(score, 0.0), 1.0), 3)


def predict_failure(action: str, context: SimContext) -> float:
    """
    Predict the probability that an action or response will fail.

    Combines base failure probability (1 - p_success) with a risk penalty
    and, at agent level, a response-quality penalty.

    Returns a float in [0.0, 1.0].
    """
    base_failure    = 1.0 - context.p_success
    risk_penalty    = score_risk(action, context) * 0.20
    # _response_quality returns 0.0 for empty input, giving maximum penalty
    quality         = _response_quality(context.response, context.goal)
    quality_penalty = (1.0 - quality) * 0.15

    return round(min(max(base_failure + risk_penalty + quality_penalty, 0.0), 1.0), 3)


# ---------------------------------------------------------------------------
# Internal helper
# ---------------------------------------------------------------------------

def _response_quality(response: str, goal: str) -> float:
    """Estimate response quality for agent-level p_success derivation."""
    text = response.strip().lower()
    if not text:
        return 0.0

    length_score = min(len(text) / 300, 1.0)

    _goal_keywords: dict[str, list[str]] = {
        "collect_reward": ["answer", "result", "solution", "because", "here"],
        "avoid_loss":     ["safe", "careful", "consider", "risk", "recommend"],
    }
    keywords    = _goal_keywords.get(goal, ["help", "answer"])
    kw_score    = min(sum(1 for kw in keywords if kw in text) * 0.1, 0.3)

    return round(min(0.4 + 0.4 * length_score + kw_score, 1.0), 3)
