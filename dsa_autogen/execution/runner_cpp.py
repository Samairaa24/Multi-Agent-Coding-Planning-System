"""
C++ Code Execution Runner: compilation + native execution + crash/test failure diagnostics.
"""

from __future__ import annotations

import asyncio
import tempfile
import time
from pathlib import Path
from typing import Optional

from dsa_autogen.models import ExecutionResult, ExecutionStatus, Language
from dsa_autogen.execution.compiler import CppCompiler
from dsa_autogen.execution.sanitizer import parse_test_results


class CppRunner:
    """Compiles and executes C++ solutions with timeout enforcement and diagnostic capture."""

    def __init__(
        self,
        compiler: Optional[CppCompiler] = None,
        workspace_dir: Optional[Path] = None,
    ):
        self.compiler = compiler or CppCompiler()
        self.workspace_dir = workspace_dir or Path(tempfile.gettempdir()) / "dsa_cpp_exec"
        self.workspace_dir.mkdir(parents=True, exist_ok=True)

    async def run(self, code: str, timeout_sec: float = 8.0) -> ExecutionResult:
        source_path = self.workspace_dir / f"solution_{int(time.time() * 1000)}.cpp"
        exe_path: Optional[Path] = None

        try:
            source_path.write_text(code, encoding="utf-8")

            # 1. Compilation Stage
            comp_start = time.perf_counter()
            comp_res = self.compiler.compile(source_path, output_dir=self.workspace_dir)
            comp_duration_ms = (time.perf_counter() - comp_start) * 1000

            if not comp_res.success or comp_res.executable_path is None:
                return ExecutionResult(
                    language=Language.CPP,
                    status=ExecutionStatus.COMPILE_ERROR,
                    exit_code=comp_res.returncode,
                    stdout=comp_res.stdout,
                    stderr=comp_res.stderr,
                    duration_ms=comp_duration_ms,
                    error_message=f"Compilation Failed with {self.compiler.compiler_path}:\n{comp_res.stderr.strip()}",
                )

            exe_path = comp_res.executable_path

            # 2. Execution Stage
            start_time = time.perf_counter()
            try:
                proc = await asyncio.create_subprocess_exec(
                    str(exe_path),
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
                    language=Language.CPP,
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
                    language=Language.CPP,
                    status=ExecutionStatus.TIMEOUT,
                    exit_code=-9,
                    stdout="",
                    stderr=f"Execution timed out after {timeout_sec:.1f} seconds. Check for infinite loops or non-optimal complexity.",
                    duration_ms=duration_ms,
                    error_message=f"Time Limit Exceeded ({timeout_sec:.1f}s)",
                )

        finally:
            # Clean up source and binary
            if source_path.exists():
                try:
                    source_path.unlink()
                except Exception:
                    pass
            if exe_path and exe_path.exists():
                try:
                    exe_path.unlink()
                except Exception:
                    pass

