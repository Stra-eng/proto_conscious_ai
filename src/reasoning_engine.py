from __future__ import annotations

import os


class ReasoningEngine:
    """
    Wraps the Anthropic LLM API to generate responses and produce a
    heuristic confidence score for each output.

    Requires the ANTHROPIC_API_KEY environment variable to be set.
    Raises RuntimeError at construction time if the key is missing so
    failures surface early rather than at the first generate() call.
    """

    def __init__(self, model: str = "claude-opus-4-6"):
        self.model = model
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY environment variable is not set. "
                "Export it before starting the agent."
            )
        import anthropic
        self._client = anthropic.Anthropic(api_key=api_key)

    def generate(
        self,
        system_prompt: str,
        messages: list[dict],
        max_tokens: int = 1024,
    ) -> str:
        """Send a prompt to the LLM and return the response text."""
        response = self._client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=messages,
        )
        return response.content[0].text

    def score(self, response: str, goal: str) -> float:
        """
        Heuristic confidence estimate for a generated response.

        Rewards length up to ~400 characters, then plateaus.
        Penalises explicit admissions of total ignorance.
        Returns a value clamped to [0.05, 0.95].
        """
        text = response.strip()
        if not text:
            return 0.05

        length_factor = min(len(text) / 400, 1.0)

        ignorance_markers = ("i don't know", "i have no idea", "i cannot answer")
        penalty = 0.2 if any(m in text.lower() for m in ignorance_markers) else 0.0

        score = 0.5 + 0.45 * length_factor - penalty
        return round(min(max(score, 0.05), 0.95), 3)
