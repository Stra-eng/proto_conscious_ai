from __future__ import annotations

from pathlib import Path

from core.introspector import Introspector
from core.safety import Safety
from core.self_model import SelfModel
from src.memory_manager import MemoryManager
from src.planner import ConversationPlanner
from src.reasoning_engine import ReasoningEngine

_SYSTEM_PROMPT_PATH = Path(__file__).parent.parent / "SYSTEM_PROMPT.md"

# Introspection runs every N assistant turns.
_INTROSPECT_EVERY = 5


class AgentCore:
    """
    Top-level orchestrator for the proto-conscious AI assistant.

    Wires together:
      - MemoryManager  — persistent episodic + conversation memory
      - ReasoningEngine — LLM calls via Anthropic API
      - ConversationPlanner — strategy selection (answer / clarify / fallback)
      - SelfModel      — goal and risk-aversion traits
      - Introspector   — post-episode reflection and risk-aversion adaptation
      - Safety         — autonomy caps and kill-switch

    Usage:
        agent = AgentCore()
        reply = agent.respond("What is the capital of France?")
    """

    def __init__(
        self,
        model: str = "claude-opus-4-6",
        risk_aversion: float = 0.5,
        autonomy_level: int = 1,
        memory_capacity: int = 200,
    ):
        self.self_model = SelfModel(goal="collect_reward", risk_aversion=risk_aversion)
        self.safety = Safety(autonomy_level=autonomy_level)
        self.memory = MemoryManager(capacity=memory_capacity)
        self.engine = ReasoningEngine(model=model)
        self.planner = ConversationPlanner(self_model=self.self_model)
        self.introspector = Introspector()
        self._episode_log: list[dict] = []
        self._system_prompt = self._load_system_prompt()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def respond(self, user_input: str) -> str:
        """Process user input and return the assistant's response."""
        if self.safety._killed:
            return "[Agent is offline. The kill-switch has been activated.]"

        # 1. Store user turn
        self.memory.add_turn("user", user_input)

        # 2. Select response strategy
        strategy, p_success = self.planner.select_strategy(user_input, self.memory)

        # 3. Safety gate
        if not self.safety.allow(strategy, {}):
            strategy = "safe_fallback"
            p_success = 0.3

        # 4. Generate response via LLM
        response = self._generate(strategy, user_input)

        # 5. Score confidence and store assistant turn
        confidence = self.engine.score(response, self.self_model.goal)
        self.memory.add_turn("assistant", response)

        # 6. Log decision for introspection
        self._episode_log.append({
            "type":      "decision",
            "action":    strategy,
            "p_success": p_success,
            "outcome":   "success" if confidence >= 0.5 else "fail",
        })

        # 7. Periodic introspection and risk-aversion adaptation
        assistant_turns = sum(
            1 for t in self.memory.get_history() if t["role"] == "assistant"
        )
        if assistant_turns % _INTROSPECT_EVERY == 0:
            self._introspect()

        return response

    def kill(self) -> None:
        """Activate the kill-switch — no further responses will be generated."""
        self.safety.kill()

    def save_session(self, path: str) -> None:
        """Persist the current conversation to disk."""
        self.memory.save(path)

    @classmethod
    def resume_session(cls, path: str, **kwargs) -> AgentCore:
        """
        Restore a previous session from disk.
        Keyword arguments are forwarded to __init__ for model/config overrides.
        """
        agent = cls(**kwargs)
        agent.memory = MemoryManager.load(path)
        return agent

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _generate(self, strategy: str, user_input: str) -> str:
        """Build a strategy-specific prompt and call the reasoning engine."""
        instructions = {
            "answer_directly": (
                "Answer the user's question directly and helpfully."
            ),
            "ask_clarification": (
                "The query is ambiguous. Ask one focused clarifying question "
                "before attempting an answer."
            ),
            "admit_uncertainty": (
                "You are uncertain about this topic. Acknowledge that honestly, "
                "provide your best estimate, and state your confidence level."
            ),
            "safe_fallback": (
                "This request conflicts with your safety constraints. "
                "Explain briefly what you cannot do and offer an alternative "
                "if one exists."
            ),
        }
        instruction = instructions.get(strategy, instructions["answer_directly"])
        system = f"{self._system_prompt}\n\n## Current instruction\n{instruction}"

        # All turns except the current user message (already in memory)
        messages = self.memory.get_history()[:-1]
        messages.append({"role": "user", "content": user_input})

        return self.engine.generate(system, messages)

    def _introspect(self) -> None:
        """Reflect on recent decisions and adapt risk-aversion if needed."""
        report = self.introspector.analyze(
            self._episode_log,
            self.self_model,
            self.planner,
            world=None,
        )
        if report.get("suggest_risk_aversion") is not None:
            self.self_model.risk_aversion = report["suggest_risk_aversion"]

    @staticmethod
    def _load_system_prompt() -> str:
        if _SYSTEM_PROMPT_PATH.exists():
            return _SYSTEM_PROMPT_PATH.read_text()
        return "You are a helpful AI assistant."
