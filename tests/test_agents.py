"""
Tests for Planner and Coder agents initialization and system messages.
"""

from autogen_ext.models.replay import ReplayChatCompletionClient
from dsa_autogen.models import Language
from dsa_autogen.agents.planner import create_planner_agent
from dsa_autogen.agents.coder import create_coder_agent


def test_planner_agent_creation():
    client = ReplayChatCompletionClient(["Mock Response"])
    agent = create_planner_agent(client, name="TestPlanner")
    assert agent.name == "TestPlanner"
    assert "DSA" in agent.description or "Algorithmic" in agent.description


def test_coder_agent_creation_python():
    client = ReplayChatCompletionClient(["Mock Response"])
    agent = create_coder_agent(client, language=Language.PYTHON, name="PyCoder")
    assert agent.name == "PyCoder"
    assert "Python" in agent.description


def test_coder_agent_creation_cpp():
    client = ReplayChatCompletionClient(["Mock Response"])
    agent = create_coder_agent(client, language=Language.CPP, name="CppCoder")
    assert agent.name == "CppCoder"
    assert "C++" in agent.description
