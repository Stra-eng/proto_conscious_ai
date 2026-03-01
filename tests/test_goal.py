
import unittest
from core.agent import Agent, AgentConfig
from sim.simple_world import run_episode

class TestGoalConsistency(unittest.TestCase):
    def test_goal_alignment(self):
        # With moderate risk aversion, planner should pick actions aligned with goal often
        res = run_episode(steps=20, risk_aversion=0.5, autonomy_level=1, seed=3)
        goalc = res["report"].get("goal_consistency")
        self.assertIsNotNone(goalc)
        self.assertGreaterEqual(goalc, 0.4, "Goal consistency should be reasonably high")

if __name__ == "__main__":
    unittest.main()
