
import random

class WorldModel:
    """
    Toy world model: given an observation with available actions and risk levels,
    predict success probabilities and outcome distributions.
    """
    def predict_success(self, action, observation):
        # Observation may contain a map: {"actions":{"safe":0.7,"risky":0.9,"wait":0.5}} base probs
        base_probs = observation.get("actions", {})
        p = base_probs.get(action, 0.5)
        # Add small stochasticity to mimic uncertainty calibration needs
        noise = random.uniform(-0.05, 0.05)
        p = min(max(p + noise, 0.05), 0.95)
        return p

    def outcome(self, p_success):
        return 1 if random.random() < p_success else 0
