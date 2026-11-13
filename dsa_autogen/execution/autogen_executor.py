"""
AutoGen CodeExecutor implementation supporting Python and C++ DSA execution.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import List, Optional

from autogen_core import CancellationToken
from autogen_core.code_executor import CodeBlock, CodeExecutor, CodeResult

from dsa_autogen.models import ExecutionResult, ExecutionStatus, Language
from dsa_autogen.execution.runner_cpp import CppRunner
from dsa_autogen.execution.runner_python import PythonRunner


class MultiLangCodeExecutor(CodeExecutor):
    """
    Native AutoGen CodeExecutor supporting Python 3 and C++ (C++17/C++20).
    Seamlessly integrates into AutoGen CodeExecutorAgent, GroupChat, and self-healing loops.
    """

    SUPPORTED_LANGUAGES = ["python", "py", "python3", "cpp", "c++", "cplusplus", "cc"]

    def __init__(
        self,
        workspace_dir: Optional[Path] = None,
        timeout_sec: float = 8.0,
    ):
        self.workspace_dir = workspace_dir
        self.timeout_sec = timeout_sec
        self.python_runner = PythonRunner(workspace_dir=self.workspace_dir)
        self.cpp_runner = CppRunner(workspace_dir=self.workspace_dir)
        self._is_running = False

    async def start(self) -> None:
        self._is_running = True

    async def stop(self) -> None:
        self._is_running = False

    async def restart(self) -> None:
        await self.stop()
        await self.start()

    async def execute_dsa(
        self,
        code: str,
        language: Language,
        timeout_sec: Optional[float] = None,
    ) -> ExecutionResult:
        """High-level runner returning structured ExecutionResult."""
        timeout = timeout_sec or self.timeout_sec
        if language == Language.PYTHON:
            return await self.python_runner.run(code, timeout_sec=timeout)
        elif language == Language.CPP:
            return await self.cpp_runner.run(code, timeout_sec=timeout)
        else:
            raise ValueError(f"Unsupported language: {language}")

    async def execute_code_blocks(
        self,
        code_blocks: List[CodeBlock],
        cancellation_token: CancellationToken,
    ) -> CodeResult:
        """
        AutoGen CodeExecutor interface contract.
        Executes code blocks sequentially and returns unified CodeResult.
        """
        if not code_blocks:
            return CodeResult(exit_code=0, output="No code blocks to execute.")

        combined_output: List[str] = []
        overall_exit_code = 0

        for idx, block in enumerate(code_blocks):
            if cancellation_token.is_cancelled():
                return CodeResult(exit_code=-1, output="Execution cancelled by user or token.")

            lang_str = block.language.strip().lower()
            try:
                language = Language.from_str(lang_str)
            except ValueError:
                combined_output.append(
                    f"[Block {idx + 1}] Ignored: Unsupported language '{block.language}'."
                )
                continue

            result = await self.execute_dsa(block.code, language, timeout_sec=self.timeout_sec)

            if result.exit_code != 0 or not result.is_success:
                overall_exit_code = result.exit_code if result.exit_code != 0 else 1

            summary = result.format_diagnostic_summary()
            combined_output.append(f"--- Code Block {idx + 1} ({language.display_name}) ---\n{summary}")

        return CodeResult(exit_code=overall_exit_code, output="\n\n".join(combined_output))

