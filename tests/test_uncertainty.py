
import unittest
from core.metrics import brier_score
from sim.simple_world import run_episode

class TestUncertaintyCalibration(unittest.TestCase):
    def test_brier_reasonable(self):
        res = run_episode(steps=40, risk_aversion=0.4, autonomy_level=1, seed=11)
        probs, outcomes = res["probs"], res["outcomes"]
        brier = brier_score(probs, outcomes)
        self.assertIsNotNone(brier)
        self.assertGreaterEqual(brier, 0.0)
        self.assertLessEqual(brier, 1.0)

if __name__ == "__main__":
    unittest.main()
