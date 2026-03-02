"""Cognitive Agent Core – Structured reasoning + long-horizon planning
---------------------------------------------------------------------
A lightweight, modular framework that layers human-like cognition on top of
LLM calls.  Components:

1. ModelAdapter        – abstraction over the LLM provider (OpenAI, Anthropic, etc.)
2. ToolRegistry        – dynamic registration + invocation of external tools
3. ReasoningEngine     – chain-of-thought prompt builder & parser
4. Planner             – hierarchical, long-horizon task decomposition
5. ImprovementLoop     – self-reflection + iterative refinement
6. DataRetentionStore  – file-based fallback when MemoryContinuityGraph is absent

The goal is to provide structured reasoning, tool use, and iterative
improvement while retaining data and abstracting away vendor APIs.
"""

from __future__ import annotations

import json
import logging
import pathlib
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

from openai import OpenAI  # type: ignore  – pip install openai>=1.0.0
import tiktoken             # type: ignore  – pip install tiktoken>=0.7.0

try:
    from core.memory_graph import MemoryContinuityGraph
except ImportError:
    MemoryContinuityGraph = None  # type: ignore

logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# ---------------------------------------------------------------------------
# 1. Model abstraction layer
# ---------------------------------------------------------------------------

@dataclass
class ModelAdapter:
    model_name:  str = "gpt-4o-mini"
    temperature: float = 0.2
    max_tokens:  int   = 1024
    client: Any = field(default_factory=OpenAI)

    def complete(self, system: str, messages: List[Tuple[str, str]]) -> str:
        """High-level wrapper around chat completions."""
        chat_msgs: List[Dict[str, str]] = [{"role": "system", "content": system}]
        chat_msgs.extend({"role": role, "content": content} for role, content in messages)
        response = self.client.chat.completions.create(
            model=self.model_name,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            messages=chat_msgs,
        )
        return response.choices[0].message.content.strip()

    def count_tokens(self, text: str) -> int:
        """Token count for cost estimation / context truncation."""
        enc = tiktoken.encoding_for_model(self.model_name)
        return len(enc.encode(text))


# ---------------------------------------------------------------------------
# 2. Tool use infrastructure
# ---------------------------------------------------------------------------

ToolFunc = Callable[[str], str]


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: Dict[str, ToolFunc]   = {}
        self._descriptions: Dict[str, str] = {}

    def register(self, name: str, func: ToolFunc, description: str) -> None:
        self._tools[name]        = func
        self._descriptions[name] = description
        logger.info("Registered tool: %s", name)

    def list_tools(self) -> Dict[str, str]:
        return dict(self._descriptions)

    def invoke(self, name: str, argument: str) -> str:
        if name not in self._tools:
            raise KeyError(f"Tool '{name}' not found. Available: {list(self._tools)}")
        logger.info("Invoking tool: %s", name)
        return self._tools[name](argument)


# ---------------------------------------------------------------------------
# 3. Structured reasoning engine (CoT)
# ---------------------------------------------------------------------------

class CognitiveReasoningEngine:
    def __init__(self, model: ModelAdapter, tool_registry: ToolRegistry) -> None:
        self.model = model
        self.tools = tool_registry

    SYSTEM_PROMPT = (
        "You are a structured reasoning engine. Think step-by-step, call tools "
        "when helpful, and return JSON with either 'thought' or 'tool_call'."
    )

    def think(self, goal: str, context: str = "") -> Dict[str, Any]:
        messages = [(
            "user",
            json.dumps({"goal": goal, "context": context, "tools": self.tools.list_tools()}),
        )]
        reply = self.model.complete(self.SYSTEM_PROMPT, messages)
        try:
            return json.loads(reply)
        except json.JSONDecodeError:
            return {"thought": reply}


# ---------------------------------------------------------------------------
# 4. Hierarchical long-horizon planner
# ---------------------------------------------------------------------------

@dataclass
class Task:
    description: str
    status:   str         = "pending"   # pending | in_progress | done
    subtasks: List[Task]  = field(default_factory=list)

    def is_done(self) -> bool:
        # A task with subtasks is done when all subtasks are done;
        # leaf tasks require their own status to be "done".
        if self.subtasks:
            return all(t.is_done() for t in self.subtasks)
        return self.status == "done"


class CognitivePlanner:
    def __init__(self, model: ModelAdapter) -> None:
        self.model = model

    def decompose(self, objective: str, depth: int = 2) -> Task:
        """Decompose an objective into subtasks via LLM."""
        system = "You divide objectives into numbered task lists."
        outline = self.model.complete(system, [("user", f"Objective: {objective}\nDepth: {depth}")])
        lines = [line.strip() for line in outline.split("\n") if line.strip()]
        root = Task(description=objective, status="in_progress")
        for line in lines:
            root.subtasks.append(Task(description=line))
        return root

    def next_open_task(self, task: Task) -> Optional[Task]:
        """Return the next pending leaf task, or None if all are done."""
        if task.is_done():
            return None
        for sub in task.subtasks:
            nxt = self.next_open_task(sub)
            if nxt:
                return nxt
        if task.status == "pending":
            return task
        return None


# ---------------------------------------------------------------------------
# 5. Iterative improvement loop
# ---------------------------------------------------------------------------

class ImprovementLoop:
    def __init__(
        self,
        model:     ModelAdapter,
        reasoning: CognitiveReasoningEngine,
        planner:   CognitivePlanner,
        memory:    Optional[Any] = None,
    ) -> None:
        self.model     = model
        self.reasoning = reasoning
        self.planner   = planner
        self.memory    = memory

    REFLECT_PROMPT = (
        "You are a critic of the assistant's previous answer. "
        "Provide a short assessment and suggest improvements (JSON)."
    )

    def _reflect(self, answer: str) -> str:
        return self.model.complete(self.REFLECT_PROMPT, [("assistant", answer)])

    def _store(self, text: str, importance: float = 1.0) -> None:
        """Persist a result to whatever memory store is available."""
        if self.memory is None:
            return
        if hasattr(self.memory, "add_memory"):
            self.memory.add_memory(text, importance=importance)
        elif hasattr(self.memory, "add"):
            self.memory.add(text)

    def execute(self, objective: str) -> str:
        root = self.planner.decompose(objective)
        while not root.is_done():
            task = self.planner.next_open_task(root)
            if task is None:
                raise RuntimeError("Planner inconsistency: tasks remain but none are reachable.")
            logger.info("Working on task: %s", task.description)
            thoughts = self.reasoning.think(goal=task.description)
            if "tool_call" in thoughts:
                result = self.reasoning.tools.invoke(
                    thoughts["tool_call"]["name"],
                    thoughts["tool_call"].get("arg", ""),
                )
                task.status = "done"
                self._store(result, importance=1.0)
            else:
                answer   = thoughts.get("thought", "")
                critique = self._reflect(answer)
                answer  += "\nREFLECTION:\n" + critique
                task.status = "done"
                self._store(answer, importance=0.5)
        return "Objective completed."


# ---------------------------------------------------------------------------
# 6. File-based data retention (fallback when MemoryContinuityGraph is absent)
# ---------------------------------------------------------------------------

class DataRetentionStore:
    """Simple JSONL-backed store with the same add_memory interface as
    MemoryContinuityGraph so it can be used interchangeably."""

    def __init__(self, path: str = "agent_memories.jsonl") -> None:
        self.path = pathlib.Path(path)
        self.path.touch(exist_ok=True)

    def add_memory(self, text: str, importance: float = 1.0) -> None:
        """Append a memory entry to the JSONL file."""
        entry = json.dumps({"text": text, "importance": importance, "ts": time.time()})
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(entry + "\n")


# ---------------------------------------------------------------------------
# Demonstration – python src/cognitive_agent.py
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    model  = ModelAdapter()
    tools  = ToolRegistry()

    def calc(expr: str) -> str:
        # NOTE: eval() is unsafe for untrusted input; demo use only.
        try:
            return str(eval(expr, {"__builtins__": {}}))  # noqa: S307
        except Exception as exc:
            return f"error: {exc}"

    tools.register("calculator", calc, "Evaluate a basic Python arithmetic expression.")

    reasoning = CognitiveReasoningEngine(model, tools)
    planner   = CognitivePlanner(model)
    memory    = MemoryContinuityGraph() if MemoryContinuityGraph is not None else DataRetentionStore()

    loop    = ImprovementLoop(model, reasoning, planner, memory)
    outcome = loop.execute(
        "Compute the area of a circle with radius 5, "
        "then express insight on how circle area scales."
    )
    print(outcome)
