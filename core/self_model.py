
class SelfModel:
    """Maintains a compact self-description (goals, traits) and predicts likely choices."""
    def __init__(self, goal="collect_reward", risk_aversion=0.3):
        self.goal = goal
        self.risk_aversion = risk_aversion  # 0..1 higher = safer choices

    def describe(self):
        return {
            "goal": self.goal,
            "traits": {
                "risk_aversion": self.risk_aversion
            }
        }

    def predict_choice_style(self):
        if self.risk_aversion >= 0.6:
            return "safe_preferring"
        elif self.risk_aversion <= 0.2:
            return "risk_taking"
        else:
            return "balanced"
