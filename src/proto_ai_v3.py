"""ProtoAI v3 — Cognitive Stack
================================
This module layers a proto-conscious cognition pipeline on top of large-language-
model calls.  It orchestrates perception → memory → self-model update → structured
reasoning → confidence calibration → outcome simulation → response emission →
reflection → memory consolidation.

External dependencies (same as previous modules):
    pip install openai tiktoken sentence_transformers networkx numpy

It re-uses existing MemoryContinuityGraph and Cognitive Agent Core components.
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List

from cognitive_agent import (
    CognitivePlanner as Planner,
    CognitiveReasoningEngine as ReasoningEngine,
    ModelAdapter,
    ToolRegistry,
)
from core.memory_graph import MemoryContinuityGraph

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logger = logging.getLogger("ProtoAIv3")
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# ---------------------------------------------------------------------------
# 1. Self-Model
# ---------------------------------------------------------------------------

@dataclass
class SelfModel:
    """Tracks agent's internal state & traits, updated after each turn."""

    identity: str = "ProtoAI v3"
    mood: str = "neutral"
    goals: List[str] = field(default_factory=list)
    last_updated: float = field(default_factory=time.time)

    def update(self, reflection: str) -> None:
        """Very naive update: detect mood keywords & increment timestamp."""
        if any(word in reflection.lower() for word in ["error", "fail", "frustrate"]):
            self.mood = "concerned"
        elif any(word in reflection.lower() for word in ["success", "good", "great"]):
            self.mood = "satisfied"
        self.last_updated = time.time()
        logger.debug("Self-model mood → %s", self.mood)


# ---------------------------------------------------------------------------
# 2. Confidence calibration
# ---------------------------------------------------------------------------

class ConfidenceCalibrator:
    """Heuristic confidence score based on length & presence of epistemic tokens."""

    LOW_MARKERS = {"maybe", "possibly", "uncertain", "not sure", "guess"}

    @staticmethod
    def score(text: str) -> float:
        tokens = text.split()
        ragged = any(tok.lower().strip(",.?") in ConfidenceCalibrator.LOW_MARKERS for tok in tokens)
        length_penalty = max(0.0, 1.0 - len(tokens) / 5000)
        base = 0.9 if not ragged else 0.6
        return round(base * length_penalty, 3)


# ---------------------------------------------------------------------------
# 3. Outcome simulator (stub)
# ---------------------------------------------------------------------------

class OutcomeSimulator:
    """Delegate short simulation to the LLM—can be expanded later."""

    def __init__(self, model: ModelAdapter) -> None:
        self.model = model

    def simulate(self, thought: str) -> str:
        prompt = (
            "You are an internal simulator. Given the planned answer below, "
            "briefly forecast (<=3 sentences) how a user might react or what "
            "consequences might ensue."
        )
        summary = self.model.complete(prompt, [("assistant", thought)])
        return summary.strip()


# ---------------------------------------------------------------------------
# 4. ProtoAI v3 orchestrator
# ---------------------------------------------------------------------------

class ProtoAI:
    def __init__(self) -> None:
        self.model = ModelAdapter()
        self.memory = MemoryContinuityGraph()
        self.tools = ToolRegistry()
        self.reasoning = ReasoningEngine(self.model, self.tools)
        self.planner = Planner(self.model)
        self.self_model = SelfModel()
        self.calibrator = ConfidenceCalibrator()
        self.simulator = OutcomeSimulator(self.model)

    # ------------------------------------------------------------------
    # Main interaction
    # ------------------------------------------------------------------

    def respond(self, user_input: str, top_k_mem: int = 5) -> Dict[str, Any]:
        # 1. Retrieve relevant memories
        retrieved = self.memory.retrieve(user_input, top_k=top_k_mem)
        context_blob = "\n".join(c for _, c, _ in retrieved)

        # 2. Update self-model (pre-context)
        self.self_model.update("initial turn")

        # 3. Structured reasoning / tool loop → produce draft
        thoughts = self.reasoning.think(goal=user_input, context=context_blob)
        if "tool_call" in thoughts:
            tool_out = self.reasoning.tools.invoke(
                thoughts["tool_call"]["name"], thoughts["tool_call"].get("arg", "")
            )
            draft = tool_out
        else:
            draft = thoughts.get("thought", "")

        # 4. Confidence calibration
        confidence = self.calibrator.score(draft)

        # 5. Simulate outcomes
        outcomes = self.simulator.simulate(draft)

        # 6. Reflection & improvement (one iteration)
        reflection_resp = self.model.complete(
            "You are a reflection module. Critique the answer and propose a better version if needed.",
            [("assistant", draft)],
        )
        improved = reflection_resp or draft

        # 7. Store structured memory update
        mem_record = json.dumps(
            {
                "user": user_input,
                "response": improved,
                "confidence": confidence,
                "outcomes": outcomes,
                "timestamp": time.time(),
            }
        )
        self.memory.add_memory(mem_record, importance=0.8)

        # 8. Update self-model with reflection text
        self.self_model.update(reflection_resp)

        return {
            "response": improved,
            "confidence": confidence,
            "predicted_outcomes": outcomes,
        }


# ---------------------------------------------------------------------------
# CLI demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    ai = ProtoAI()
    print("ProtoAI v3 interactive demo. Type 'quit' to exit.")
    while True:
        text = input("You  > ").strip()
        if text.lower() in {"quit", "exit"}:
            break
        result = ai.respond(text)
        print(
            f"ProtoAI > {result['response']}\n"
            f"(confidence={result['confidence']}, outcomes={result['predicted_outcomes']})\n"
        )
