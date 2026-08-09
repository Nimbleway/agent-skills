"""Normalized agent trace shared by Claude and Codex backends."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field


class NormalizedTrace(BaseModel):
    runtime: Literal["claude", "codex"]
    model: str
    effort: str | None = None
    prompt: str
    triggered_skills: list[str] = Field(default_factory=list)
    tools_called: list[str] = Field(default_factory=list)
    tool_names: list[str] = Field(default_factory=list)
    response: str = ""
    final_response: str = ""
    asked_clarify: bool = False
    error: str | None = None
    raw_path: Path | None = None
    cost_usd: float | None = None
    num_turns: int | None = None
    usage: dict[str, Any] | None = None

    def model_post_init(self, __context: Any) -> None:
        if not self.final_response and self.response:
            self.final_response = self.response
        if not self.tool_names and self.tools_called:
            # Product-style names used by first_turn_action / tool_selection
            self.tool_names = list(self.tools_called)
