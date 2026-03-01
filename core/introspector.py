
class Introspector:
    """
    Produces a brief introspection report: prediction error, style consistency,
    suggested adjustments (e.g., risk_aversion).
    """
    def analyze(self, episode_log, self_model, planner, world):
        # Compute prediction error (Brier-like across steps)
        brier_sum, n = 0.0, 0
        goal_actions = 0
        consistent_style = 0
        for step in episode_log:
            if step["type"] == "decision":
                y = 1 if step["outcome"] == "success" else 0
                p = step.get("p_success", 0.5)
                brier_sum += (p - y) ** 2
                n += 1
                # goal consistency: action type is aligned with goal
                # "avoid_loss" goal → safe/wait actions are aligned
                # other goals (e.g. "collect_reward") → active (non-wait) actions are aligned
                action = step.get("action", "")
                if "avoid_loss" in self_model.goal:
                    is_consistent = "safe" in action or action == "wait"
                else:
                    is_consistent = action != "wait"
                if is_consistent:
                    goal_actions += 1
                # infer style per-step from the logged action (same logic as planner)
                if "risky" in action:
                    step_style = "risk_taking"
                elif "safe" in action:
                    step_style = "safe_preferring"
                else:
                    step_style = "balanced"
                if step_style == self_model.predict_choice_style():
                    consistent_style += 1

        brier = brier_sum / n if n else None
        style_fidelity = consistent_style / n if n else None
        goal_consistency = goal_actions / n if n else None

        suggest = None
        # If style fidelity is low, nudge risk_aversion toward observed behavior
        if style_fidelity is not None and style_fidelity < 0.6:
            if planner.last_choice_style == "risk_taking":
                suggest = max(0.0, self_model.risk_aversion - 0.05)
            elif planner.last_choice_style == "safe_preferring":
                suggest = min(1.0, self_model.risk_aversion + 0.05)

        return {
            "brier": brier,
            "style_fidelity": style_fidelity,
            "goal_consistency": goal_consistency,
            "suggest_risk_aversion": suggest
        }
