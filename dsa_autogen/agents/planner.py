"""
Planner Agent: Responsible for problem decomposition, optimal complexity analysis,
and test case generation.
"""

from __future__ import annotations

from typing import Optional
from autogen_agentchat.agents import AssistantAgent
from autogen_core.models import ChatCompletionClient

from dsa_autogen.agents.prompts import PLANNER_SYSTEM_PROMPT


def create_planner_agent(
    model_client: ChatCompletionClient,
    name: str = "Planner",
    system_prompt: Optional[str] = None,
) -> AssistantAgent:
    """Factory creating an AutoGen AssistantAgent configured as Algorithmic Planner."""
    return AssistantAgent(
        name=name,
        model_client=model_client,
        system_message=system_prompt or PLANNER_SYSTEM_PROMPT,
        description=(
            "Expert Algorithmic Architect who analyzes DSA problems, specifies optimal time/space complexity, "
            "identifies edge cases, and designs exhaustive verification test cases."
        ),
    )
