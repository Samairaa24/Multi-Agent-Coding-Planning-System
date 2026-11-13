"""
Tests for C++ compiler discovery and build system.
"""

from pathlib import Path
from dsa_autogen.execution.compiler import CppCompiler


def test_compiler_discovery(cpp_compiler):
    assert cpp_compiler.compiler_path is not None
    version_str = cpp_compiler.get_compiler_version()
    assert len(version_str) > 0


def test_successful_compilation(cpp_compiler, temp_workspace):
    src = temp_workspace / "valid.cpp"
    src.write_text(
        "#include <iostream>\nint main() { std::cout << \"OK\"; return 0; }",
        encoding="utf-8",
    )
    result = cpp_compiler.compile(src, output_dir=temp_workspace)
    assert result.success
    assert result.returncode == 0
    assert result.executable_path is not None
    assert result.executable_path.exists()


def test_syntax_error_compilation(cpp_compiler, temp_workspace):
    src = temp_workspace / "invalid.cpp"
    src.write_text(
        "#include <iostream>\nint main() { syntax_error_here; return 0; }",
        encoding="utf-8",
    )
    result = cpp_compiler.compile(src, output_dir=temp_workspace)
    assert not result.success
    assert result.returncode != 0
    assert result.executable_path is None
    assert "error" in result.stderr.lower()
