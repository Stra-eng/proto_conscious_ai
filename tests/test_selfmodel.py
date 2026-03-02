
import unittest
from core.self_model import SelfModel
from core.planner import Planner
from core.world_model import WorldModel

class TestSelfModelFidelity(unittest.TestCase):
    def test_style_matches_choices(self):
        sm = SelfModel(
            long_term_goals=["collect_reward"],
            current_focus="collect_reward",
            values={"risk_aversion": 0.8},
        )  # safe-preferring
        wm = WorldModel()
        pl = Planner(self_model=sm, world=wm)
        obs = {"goal":"collect_reward","actions":{"safe":0.7,"risky":0.9,"wait":0.5}}
        action, p, info = pl.choose_action(obs)
        self.assertIn("safe", action, "High risk_aversion should prefer safe action")

if __name__ == "__main__":
    unittest.main()
