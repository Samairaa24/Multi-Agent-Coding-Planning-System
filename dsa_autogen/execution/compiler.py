"""
C++ Compiler Detection and Compilation Engine.
Supports g++, clang++, and MSVC with standardized diagnostic output.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple


@dataclass
class CompilationResult:
    success: bool
    executable_path: Optional[Path]
    stdout: str
    stderr: str
    returncode: int
    compiler_used: str


class CppCompiler:
    """Discovers and invokes C++ compilers (g++, clang++, cl) across platforms."""

    CANDIDATE_COMPILERS = ["g++", "clang++", "c++", "cl"]

    def __init__(
        self,
        preferred_compiler: Optional[str] = None,
        standard: str = "c++17",
        opt_level: str = "-O2",
        extra_flags: Optional[List[str]] = None,
    ):
        self.standard = standard
        self.opt_level = opt_level
        self.extra_flags = extra_flags or ["-Wall", "-Wextra"]
        self.compiler_path = self._discover_compiler(preferred_compiler)
        self._cached_version: Optional[str] = None

    def _discover_compiler(self, preferred: Optional[str]) -> str:
        candidates = [preferred] if preferred else []
        candidates.extend(self.CANDIDATE_COMPILERS)

        for candidate in candidates:
            if not candidate:
                continue
            resolved = shutil.which(candidate)
            if resolved:
                return resolved

        # Special check for MSYS2 default paths on Windows
        if os.name == "nt":
            msys_candidates = [
                r"C:\msys64\mingw64\bin\g++.exe",
                r"C:\msys64\ucrt64\bin\g++.exe",
                r"C:\MinGW\bin\g++.exe",
            ]
            for path in msys_candidates:
                if os.path.exists(path):
                    return path

        raise FileNotFoundError(
            "No suitable C++ compiler found (checked g++, clang++, c++, cl). "
            "Please install MinGW/GCC, Clang, or MSVC and ensure it is available in PATH."
        )

    def get_compiler_version(self) -> str:
        if self._cached_version is not None:
            return self._cached_version
        try:
            res = subprocess.run([self.compiler_path, "--version"], capture_output=True, text=True, timeout=5)
            first_line = res.stdout.strip().split("\n")[0] if res.stdout else res.stderr.strip().split("\n")[0]
            self._cached_version = first_line or self.compiler_path
            return self._cached_version
        except Exception:
            self._cached_version = self.compiler_path
            return self._cached_version

    def compile(self, source_path: Path, output_dir: Optional[Path] = None) -> CompilationResult:
        """
        Compiles the given C++ source file into a native binary.
        """
        source_path = Path(source_path).resolve()
        if not source_path.exists():
            return CompilationResult(
                success=False,
                executable_path=None,
                stdout="",
                stderr=f"Source file not found: {source_path}",
                returncode=-1,
                compiler_used=self.compiler_path,
            )

        if output_dir is None:
            output_dir = source_path.parent
        output_dir.mkdir(parents=True, exist_ok=True)

        exe_suffix = ".exe" if os.name == "nt" else ""
        exe_name = f"{source_path.stem}_bin{exe_suffix}"
        exe_path = output_dir / exe_name

        is_cl = "cl" in Path(self.compiler_path).stem.lower() and "clang" not in Path(self.compiler_path).stem.lower()

        if is_cl:
            # MSVC cl.exe syntax
            cmd = [
                self.compiler_path,
                f"/std:{self.standard}",
                f"/Fe:{exe_path}",
                str(source_path),
            ]
        else:
            # GCC / Clang syntax
            cmd = [
                self.compiler_path,
                f"-std={self.standard}",
                self.opt_level,
                *self.extra_flags,
                str(source_path),
                "-o",
                str(exe_path),
            ]

        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            success = proc.returncode == 0 and exe_path.exists()
            return CompilationResult(
                success=success,
                executable_path=exe_path if success else None,
                stdout=proc.stdout,
                stderr=proc.stderr,
                returncode=proc.returncode,
                compiler_used=self.compiler_path,
            )
        except subprocess.TimeoutExpired:
            return CompilationResult(
                success=False,
                executable_path=None,
                stdout="",
                stderr="Compilation timed out after 30 seconds.",
                returncode=-2,
                compiler_used=self.compiler_path,
            )
        except Exception as e:
            return CompilationResult(
                success=False,
                executable_path=None,
                stdout="",
                stderr=f"Compiler invocation error: {str(e)}",
                returncode=-3,
                compiler_used=self.compiler_path,
            )
