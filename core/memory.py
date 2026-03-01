
from collections import deque

class EpisodicMemory:
    """Simple bounded episodic memory with typed events and long-horizon recall."""
    def __init__(self, capacity=200):
        self.capacity = capacity
        self.events = deque(maxlen=capacity)
        self.step = 0

    def add(self, event: dict):
        """event: {"type": str, "data": any}"""
        self.step += 1
        self.events.append({"step": self.step, **event})

    def recall(self, k_steps_back=10, event_type=None):
        """Return the event ~k steps back (by step index), optionally filtered by type."""
        target = self.step - k_steps_back
        if target <= 0:
            return None
        # Find the closest event with step <= target
        best = None
        for e in reversed(self.events):
            if e["step"] <= target and (event_type is None or e["type"] == event_type):
                best = e
                break
        return best

    def all(self):
        return list(self.events)
