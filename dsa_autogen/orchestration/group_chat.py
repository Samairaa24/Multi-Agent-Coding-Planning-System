"""
AutoGen Team Integration using RoundRobinGroupChat.
Composes Planner, Coder, and CodeExecutorAgent with automatic termination.
"""

from __future__ import annotations

from typing import Optional
from autogen_agentchat.agents import CodeExecutorAgent
from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_core.models import ChatCompletionClient

from dsa_autogen.models import Language
from dsa_autogen.agents.planner import create_planner_agent
from dsa_autogen.agents.coder import create_coder_agent
from dsa_autogen.execution.autogen_executor import MultiLangCodeExecutor


def create_dsa_group_chat(
    model_client: ChatCompletionClient,
    language: Language,
    executor: Optional[MultiLangCodeExecutor] = None,
    max_messages: int = 15,
) -> RoundRobinGroupChat:
    """
    Constructs an AutoGen 0.4 RoundRobinGroupChat team consisting of:
    1. Planner: Designs algorithms and test specs.
    2. Coder: Writes Python/C++ code.
    3. CodeExecutorAgent: Runs code using MultiLangCodeExecutor.
    Terminates when 'ALL TESTS PASSED' appears or max_messages is reached.
    """
    active_executor = executor or MultiLangCodeExecutor()

    planner = create_planner_agent(model_client=model_client, name="Planner")
    coder = create_coder_agent(model_client=model_client, language=language, name="Coder")

    # CodeExecutorAgent wraps our MultiLangCodeExecutor
    executor_agent = CodeExecutorAgent(
        name="Executor",
        code_executor=active_executor,
        description="Executes generated Python or C++ code blocks and returns execution results.",
    )

    termination = (
        TextMentionTermination("ALL TESTS PASSED")
        | MaxMessageTermination(max_messages=max_messages)
    )

    team = RoundRobinGroupChat(
        participants=[planner, coder, executor_agent],
        termination_condition=termination,
    )

    return team

