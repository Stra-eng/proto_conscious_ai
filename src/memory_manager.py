from __future__ import annotations

import json
import uuid
from pathlib import Path

from core.memory import EpisodicMemory


class MemoryManager:
    """
    Conversation-level memory for the AI assistant.

    Wraps EpisodicMemory for step-based recall and maintains a structured
    turn history in LLM messages format. Supports JSON persistence so
    sessions can be saved and resumed across runs.
    """

    def __init__(self, capacity: int = 200, session_id: str | None = None):
        self.session_id = session_id or str(uuid.uuid4())[:8]
        self._episodic = EpisodicMemory(capacity=capacity)
        self._turns: list[dict] = []

    def add_turn(self, role: str, content: str) -> None:
        """Record a conversation turn and log it to episodic memory."""
        self._turns.append({"role": role, "content": content})
        self._episodic.add({"type": role, "data": content})

    def get_history(self) -> list[dict]:
        """Return the full turn history in LLM messages format."""
        return list(self._turns)

    def recall_turn(self, k_steps_back: int) -> dict | None:
        """Return the event k steps back from episodic memory."""
        return self._episodic.recall(k_steps_back=k_steps_back)

    def save(self, path: str) -> None:
        """Persist the conversation history to a JSON file."""
        data = {"session_id": self.session_id, "turns": self._turns}
        Path(path).write_text(json.dumps(data, indent=2))

    @classmethod
    def load(cls, path: str, capacity: int = 200) -> MemoryManager:
        """Resume a previous session from a JSON file."""
        data = json.loads(Path(path).read_text())
        manager = cls(capacity=capacity, session_id=data["session_id"])
        for turn in data["turns"]:
            manager.add_turn(turn["role"], turn["content"])
        return manager

    @property
    def turn_count(self) -> int:
        return len(self._turns)
