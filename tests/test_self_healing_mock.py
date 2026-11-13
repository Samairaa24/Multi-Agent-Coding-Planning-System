"""
Integration tests for end-to-end self-healing execution loop using deterministic mocks.
"""

import pytest
from dsa_autogen.models import Language, ExecutionStatus
from dsa_autogen.problems import get_problem
from dsa_autogen.mocks.mock_client import create_mock_client
from dsa_autogen.orchestration.loop import SelfHealingOrchestrator


@pytest.mark.asyncio
async def test_self_healing_python_mock(autogen_executor):
    problem = get_problem("two_sum")
    assert problem is not None

    mock_client = create_mock_client(language=Language.PYTHON, problem_title=problem.title)
    orchestrator = SelfHealingOrchestrator(
        model_client=mock_client,
        executor=autogen_executor,
        max_retries=3,
    )

    report = await orchestrator.run(problem=problem, language=Language.PYTHON)

    assert report.final_status == ExecutionStatus.SUCCESS
    assert report.total_iterations == 2
    assert report.healed
    assert "ALL TESTS PASSED" in report.final_code


@pytest.mark.asyncio
async def test_self_healing_cpp_mock(autogen_executor):
    problem = get_problem("two_sum")
    assert problem is not None

    mock_client = create_mock_client(language=Language.CPP, problem_title=problem.title)
    orchestrator = SelfHealingOrchestrator(
        model_client=mock_client,
        executor=autogen_executor,
        max_retries=3,
    )

    report = await orchestrator.run(problem=problem, language=Language.CPP)

    assert report.final_status == ExecutionStatus.SUCCESS
    assert report.total_iterations == 2
    assert report.healed
    assert "ALL TESTS PASSED" in report.final_code
