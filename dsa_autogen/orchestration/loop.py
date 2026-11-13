"""
Self-Healing Execution Loop Orchestrator.
Manages the Planner -> Coder -> Execution -> Diagnostic Feedback -> Self-Healing cycle.
"""

from __future__ import annotations

import time
from typing import Callable, List, Optional

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken
from autogen_core.models import ChatCompletionClient

from dsa_autogen.models import (
    DSAProblem,
    ExecutionResult,
    ExecutionStatus,
    Language,
    SelfHealingReport,
    SelfHealingStep,
)
from dsa_autogen.agents.planner import create_planner_agent
from dsa_autogen.agents.coder import create_coder_agent
from dsa_autogen.agents.prompts import format_self_healing_feedback
from dsa_autogen.execution.autogen_executor import MultiLangCodeExecutor
from dsa_autogen.execution.sanitizer import extract_code_blocks


class SelfHealingOrchestrator:
    """
    Orchestrates the multi-agent DSA resolution pipeline:
    1. Planner agent formulates algorithm and test specs.
    2. Coder agent generates executable solution with test runner.
    3. MultiLangCodeExecutor runs code (Python or C++).
    4. If failure/bug: error diagnostics feed back to Coder to self-heal.
    5. Repeats until ALL TESTS PASS or max retries reached.
    """

    def __init__(
        self,
        model_client: ChatCompletionClient,
        executor: Optional[MultiLangCodeExecutor] = None,
        max_retries: int = 3,
        timeout_sec: float = 8.0,
    ):
        self.model_client = model_client
        self.executor = executor or MultiLangCodeExecutor(timeout_sec=timeout_sec)
        self.max_retries = max_retries
        self.timeout_sec = timeout_sec

    async def run(
        self,
        problem: DSAProblem,
        language: Language,
        on_event: Optional[Callable[[str, str], None]] = None,
        cancellation_token: Optional[CancellationToken] = None,
    ) -> SelfHealingReport:
        token = cancellation_token or CancellationToken()
        start_wall_time = time.perf_counter()

        def emit(event_type: str, message: str) -> None:
            if on_event:
                on_event(event_type, message)

        # 1. Initialize Agents
        planner = create_planner_agent(self.model_client)
        coder = create_coder_agent(self.model_client, language)

        # 2. Stage 1: Planning
        emit("PLANNING_START", f"Planner analyzing problem: '{problem.title}'")
        problem_prompt = self._build_problem_prompt(problem, language)

        planner_response = await planner.on_messages(
            [TextMessage(content=problem_prompt, source="user")], token
        )
        plan_text = str(planner_response.chat_message.content)
        emit("PLANNING_COMPLETE", plan_text)

        # 3. Stage 2: Initial Code Generation
        emit("CODING_START", f"Coder generating initial {language.display_name} solution based on plan...")
        coder_prompt = self._build_coder_initial_prompt(problem, plan_text, language)

        coder_response = await coder.on_messages(
            [TextMessage(content=coder_prompt, source="Planner")], token
        )
        current_code_text = str(coder_response.chat_message.content)

        steps: List[SelfHealingStep] = []
        final_code = ""
        current_iteration = 1
        final_status = ExecutionStatus.RUNTIME_ERROR

        # 4. Stage 3: Self-Healing Execution Loop
        while current_iteration <= (self.max_retries + 1):
            emit("EXECUTION_START", f"Iteration #{current_iteration}: Executing solution...")

            extracted = extract_code_blocks(current_code_text, default_language=language)
            if not extracted:
                exec_result = ExecutionResult(
                    language=language,
                    status=ExecutionStatus.COMPILE_ERROR,
                    exit_code=-1,
                    error_message=f"No {language.display_name} code block found in coder response.",
                )
                code_to_run = current_code_text
            else:
                target_lang, code_to_run = extracted[0]
                exec_result = await self.executor.execute_dsa(code_to_run, target_lang, self.timeout_sec)

            final_code = code_to_run

            step = SelfHealingStep(
                iteration=current_iteration,
                language=language,
                code=code_to_run,
                execution_result=exec_result,
                agent_reasoning=current_code_text,
            )
            steps.append(step)

            # Check if execution succeeded
            if exec_result.is_success:
                emit("EXECUTION_SUCCESS", f"All tests passed on iteration #{current_iteration}!")
                final_status = ExecutionStatus.SUCCESS
                break

            # If failed and retries exhausted
            if current_iteration > self.max_retries:
                emit(
                    "MAX_RETRIES_REACHED",
                    f"Max retries ({self.max_retries}) reached without full test pass. Last status: {exec_result.status.value}",
                )
                final_status = exec_result.status
                break

            # Self-healing feedback step
            emit(
                "HEALING_TRIGGERED",
                f"Iteration #{current_iteration} failed ({exec_result.status.value}). Feeding diagnostics back to Coder...",
            )

            feedback_prompt = format_self_healing_feedback(
                status=exec_result.status.value,
                exit_code=exec_result.exit_code,
                error_message=exec_result.error_message,
                stderr=exec_result.stderr,
                stdout=exec_result.stdout,
                iteration=current_iteration,
                max_retries=self.max_retries,
                language=language,
            )
            step.feedback_prompt = feedback_prompt

            coder_fix_response = await coder.on_messages(
                [TextMessage(content=feedback_prompt, source="ExecutionJudge")], token
            )
            current_code_text = str(coder_fix_response.chat_message.content)
            emit("HEALING_PATCH_GENERATED", f"Coder generated patch for iteration #{current_iteration + 1}")

            current_iteration += 1

        total_time = time.perf_counter() - start_wall_time

        summary = (
            f"Problem '{problem.title}' resolved in {language.display_name} with status {final_status.value} "
            f"across {len(steps)} iteration(s) in {total_time:.2f}s."
        )

        return SelfHealingReport(
            problem_id=problem.id,
            problem_title=problem.title,
            language=language,
            final_status=final_status,
            total_iterations=len(steps),
            steps=steps,
            final_code=final_code,
            total_time_seconds=total_time,
            summary=summary,
        )

    def _build_problem_prompt(self, problem: DSAProblem, language: Language) -> str:
        constraints_str = "\n".join(f"- {c}" for c in problem.constraints)
        examples_str = "\n".join(
            f"Example {i+1}: Input: {ex['input']} | Output: {ex['output']}"
            for i, ex in enumerate(problem.examples)
        )
        test_cases_str = "\n".join(
            f"- {tc.name}: Input={tc.input_repr} -> Expected={tc.expected_output}"
            for tc in problem.test_cases
        )

        return f"""Please formulate an optimal algorithmic plan for the following DSA problem:

Title: {problem.title}
Target Language: {language.display_name}

Description:
{problem.description}

Constraints:
{constraints_str}

Examples:
{examples_str}

Required Test Cases to cover:
{test_cases_str}

Target Complexities:
- Time: {problem.target_time_complexity or 'Optimal'}
- Space: {problem.target_space_complexity or 'Optimal'}
"""

    def _build_coder_initial_prompt(self, problem: DSAProblem, plan: str, language: Language) -> str:
        test_cases_str = "\n".join(
            f"- {tc.name}: Input={tc.input_repr} -> Expected={tc.expected_output}"
            for tc in problem.test_cases
        )
        return f"""Implement the optimal solution in {language.display_name} for '{problem.title}' based strictly on the Architect's plan.

### Architect Plan:
{plan}

### Problem Specification:
{problem.description}

### Test Cases that MUST be embedded and verified in the code:
{test_cases_str}

Provide the complete executable code inside ```{"python" if language == Language.PYTHON else "cpp"} ... ```.
Ensure `ALL TESTS PASSED` is printed only when every test succeeds."""

