"""
Domain data models for DSA AutoGen.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class Language(str, Enum):
    PYTHON = "python"
    CPP = "cpp"

    @classmethod
    def from_str(cls, val: str) -> Language:
        normalized = val.strip().lower()
        if normalized in ("python", "py", "python3"):
            return cls.PYTHON
        if normalized in ("cpp", "c++", "cplusplus", "cc"):
            return cls.CPP
        raise ValueError(f"Unsupported language '{val}'. Supported languages are 'python' and 'cpp'.")

    @property
    def extension(self) -> str:
        return ".py" if self == Language.PYTHON else ".cpp"

    @property
    def display_name(self) -> str:
        return "Python 3" if self == Language.PYTHON else "C++17"


class ExecutionStatus(str, Enum):
    SUCCESS = "SUCCESS"
    COMPILE_ERROR = "COMPILE_ERROR"
    RUNTIME_ERROR = "RUNTIME_ERROR"
    TIMEOUT = "TIMEOUT"
    TEST_FAILURE = "TEST_FAILURE"


class TestCase(BaseModel):
    __test__ = False  # Inform pytest that this is a data model, not a test suite
    name: str = "Test Case"
    input_repr: str
    expected_output: str
    description: Optional[str] = None


class DSAProblem(BaseModel):
    id: str
    title: str
    description: str
    constraints: List[str] = Field(default_factory=list)
    examples: List[Dict[str, str]] = Field(default_factory=list)
    test_cases: List[TestCase] = Field(default_factory=list)
    starter_code: Optional[str] = None
    target_time_complexity: Optional[str] = None
    target_space_complexity: Optional[str] = None
    recommended_language: Optional[Language] = None


@dataclass
class ExecutionResult:
    language: Language
    status: ExecutionStatus
    exit_code: int
    stdout: str = ""
    stderr: str = ""
    duration_ms: float = 0.0
    error_message: Optional[str] = None
    passed_tests: int = 0
    total_tests: int = 0

    @property
    def is_success(self) -> bool:
        return self.status == ExecutionStatus.SUCCESS

    def format_diagnostic_summary(self) -> str:
        """Formatted summary tailored for agent consumption during self-healing."""
        lines = [
            f"Execution Status: {self.status.value}",
            f"Exit Code: {self.exit_code}",
            f"Execution Duration: {self.duration_ms:.2f} ms",
        ]
        if self.total_tests > 0:
            lines.append(f"Test Score: {self.passed_tests}/{self.total_tests} passed")

        if self.error_message:
            lines.append(f"\n[Primary Error]\n{self.error_message}")

        if self.stderr.strip():
            lines.append(f"\n[Compiler / Stderr Diagnostics]\n{self.stderr.strip()}")

        if self.stdout.strip():
            lines.append(f"\n[Standard Output]\n{self.stdout.strip()}")

        return "\n".join(lines)


@dataclass
class SelfHealingStep:
    iteration: int
    language: Language
    code: str
    execution_result: ExecutionResult
    feedback_prompt: Optional[str] = None
    agent_reasoning: Optional[str] = None


@dataclass
class SelfHealingReport:
    problem_id: str
    problem_title: str
    language: Language
    final_status: ExecutionStatus
    total_iterations: int
    steps: List[SelfHealingStep] = field(default_factory=list)
    final_code: str = ""
    total_time_seconds: float = 0.0
    summary: str = ""

    @property
    def healed(self) -> bool:
        return self.final_status == ExecutionStatus.SUCCESS and self.total_iterations > 1

    @property
    def passed_on_first_try(self) -> bool:
        return self.final_status == ExecutionStatus.SUCCESS and self.total_iterations == 1
