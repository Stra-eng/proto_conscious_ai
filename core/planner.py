
class Planner:
    """
    Chooses an action aligned with self_model goal and risk_aversion.
    Observation: {"actions":{"safe":p_base, "risky":p_base, "wait":p_base}, "goal":"collect_reward"}
    """
    def __init__(self, self_model, world):
        self.self_model = self_model
        self.world = world
        self.last_choice_style = None

    def choose_action(self, observation):
        goal = observation.get("goal")
        actions = list(observation.get("actions", {}).keys()) or ["wait"]
        # Score actions: weigh success prob vs risk preference
        scores = {}
        for a in actions:
            p = self.world.predict_success(a, observation)
            # Risk weighting: penalize "risky" if high risk_aversion; reward if low
            risk_tag = "risky" if "risky" in a else ("safe" if "safe" in a else "neutral")
            bias = 0.0
            if risk_tag == "risky":
                bias = -0.2 * self.self_model.risk_aversion
            elif risk_tag == "safe":
                bias = +0.1 * self.self_model.risk_aversion
            score = p + bias
            scores[a] = score

        # Pick best
        action = max(scores, key=scores.get)
        p_success = self.world.predict_success(action, observation)
        # Track style implied by choice
        if "risky" in action:
            self.last_choice_style = "risk_taking"
        elif "safe" in action:
            self.last_choice_style = "safe_preferring"
        else:
            self.last_choice_style = "balanced"
        info = {"scores": scores, "choice_style": self.last_choice_style}
        return action, p_success, info
