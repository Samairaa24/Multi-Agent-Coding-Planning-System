"""
Python Code Execution Runner with timeout, output capture, and error diagnostic parsing.
"""

from __future__ import annotations

import asyncio
import os
import sys
import tempfile
import time
from pathlib import Path
from typing import Optional

from dsa_autogen.models import ExecutionResult, ExecutionStatus, Language
from dsa_autogen.execution.sanitizer import parse_test_results


class PythonRunner:
    """Executes Python code in an isolated subprocess with timeout and error tracking."""

    def __init__(self, workspace_dir: Optional[Path] = None):
        self.workspace_dir = workspace_dir or Path(tempfile.gettempdir()) / "dsa_python_exec"
        self.workspace_dir.mkdir(parents=True, exist_ok=True)

    async def run(self, code: str, timeout_sec: float = 8.0) -> ExecutionResult:
        file_path = self.workspace_dir / f"solution_{int(time.time() * 1000)}.py"
        try:
            file_path.write_text(code, encoding="utf-8")

            start_time = time.perf_counter()
            try:
                proc = await asyncio.create_subprocess_exec(
                    sys.executable,
                    str(file_path),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=str(self.workspace_dir),
                )
                stdout_bytes, stderr_bytes = await asyncio.wait_for(
                    proc.communicate(), timeout=timeout_sec
                )
                duration_ms = (time.perf_counter() - start_time) * 1000

                stdout = stdout_bytes.decode("utf-8", errors="replace")
                stderr = stderr_bytes.decode("utf-8", errors="replace")
                exit_code = proc.returncode if proc.returncode is not None else 0

                status, passed, total, err_msg = parse_test_results(stdout, stderr, exit_code)

                return ExecutionResult(
                    language=Language.PYTHON,
                    status=status,
                    exit_code=exit_code,
                    stdout=stdout,
                    stderr=stderr,
                    duration_ms=duration_ms,
                    error_message=err_msg,
                    passed_tests=passed,
                    total_tests=total,
                )

            except asyncio.TimeoutError:
                duration_ms = (time.perf_counter() - start_time) * 1000
                try:
                    proc.kill()
                    await proc.wait()
                except Exception:
                    pass
                return ExecutionResult(
                    language=Language.PYTHON,
                    status=ExecutionStatus.TIMEOUT,
                    exit_code=-9,
                    stdout="",
                    stderr=f"Execution timed out after {timeout_sec:.1f} seconds. Check for infinite loops or non-optimal complexity.",
                    duration_ms=duration_ms,
                    error_message=f"Time Limit Exceeded ({timeout_sec:.1f}s)",
                )

        finally:
            if file_path.exists():
                try:
                    file_path.unlink()
                except Exception:
                    pass

