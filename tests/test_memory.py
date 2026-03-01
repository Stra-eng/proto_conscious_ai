
import unittest
from core.memory import EpisodicMemory

class TestMemoryContinuity(unittest.TestCase):
    def test_long_horizon_recall(self):
        mem = EpisodicMemory(capacity=50)
        for i in range(30):
            mem.add({"type":"obs","data":{"i":i}})
        ev = mem.recall(k_steps_back=20, event_type="obs")
        self.assertIsNotNone(ev, "Should recall an older observation 20 steps back")

if __name__ == "__main__":
    unittest.main()
