"""
Tests for domain data models and enums.
"""

import pytest
from dsa_autogen.models import (
    Language,
    ExecutionStatus,
    ExecutionResult,
    SelfHealingReport,
    SelfHealingStep,
    TestCase,
    DSAProblem,
)


def test_language_enum_parsing():
    assert Language.from_str("python") == Language.PYTHON
    assert Language.from_str("py") == Language.PYTHON
    assert Language.from_str("PYTHON3") == Language.PYTHON

    assert Language.from_str("cpp") == Language.CPP
    assert Language.from_str("c++") == Language.CPP
    assert Language.from_str("CPLUSPLUS") == Language.CPP

    with pytest.raises(ValueError):
        Language.from_str("java")


def test_execution_result_formatting():
    res = ExecutionResult(
        language=Language.PYTHON,
        status=ExecutionStatus.SUCCESS,
        exit_code=0,
        stdout="[TEST 1] PASS\nALL TESTS PASSED",
        duration_ms=45.2,
        passed_tests=1,
        total_tests=1,
    )
    assert res.is_success
    summary = res.format_diagnostic_summary()
    assert "SUCCESS" in summary
    assert "45.20 ms" in summary
    assert "1/1 passed" in summary


def test_self_healing_report_flags():
    step1 = SelfHealingStep(
        iteration=1,
        language=Language.PYTHON,
        code="# buggy",
        execution_result=ExecutionResult(language=Language.PYTHON, status=ExecutionStatus.TEST_FAILURE, exit_code=1),
    )
    step2 = SelfHealingStep(
        iteration=2,
        language=Language.PYTHON,
        code="# fixed",
        execution_result=ExecutionResult(language=Language.PYTHON, status=ExecutionStatus.SUCCESS, exit_code=0),
    )

    report_healed = SelfHealingReport(
        problem_id="p1",
        problem_title="Problem 1",
        language=Language.PYTHON,
        final_status=ExecutionStatus.SUCCESS,
        total_iterations=2,
        steps=[step1, step2],
    )
    assert report_healed.healed
    assert not report_healed.passed_on_first_try

    report_first_try = SelfHealingReport(
        problem_id="p2",
        problem_title="Problem 2",
        language=Language.PYTHON,
        final_status=ExecutionStatus.SUCCESS,
        total_iterations=1,
        steps=[step2],
    )
    assert report_first_try.passed_on_first_try
    assert not report_first_try.healed
