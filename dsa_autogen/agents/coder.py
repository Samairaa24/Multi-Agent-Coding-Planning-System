"""
Coder Agent: Responsible for generating robust Python and C++ DSA solutions
with built-in test runners, and performing targeted self-healing revisions.
"""

from __future__ import annotations

from typing import Optional
from autogen_agentchat.agents import AssistantAgent
from autogen_core.models import ChatCompletionClient

from dsa_autogen.models import Language
from dsa_autogen.agents.prompts import get_coder_system_prompt


def create_coder_agent(
    model_client: ChatCompletionClient,
    language: Language,
    name: str = "Coder",
    system_prompt: Optional[str] = None,
) -> AssistantAgent:
    """Factory creating an AutoGen AssistantAgent configured as DSA Coder for Python or C++."""
    prompt = system_prompt or get_coder_system_prompt(language)
    return AssistantAgent(
        name=name,
        model_client=model_client,
        system_message=prompt,
        description=(
            f"Senior {language.display_name} engineer who implements high-performance DSA solutions, "
            f"embeds automated test suites, and fixes bugs during self-healing cycles."
        ),
    )

