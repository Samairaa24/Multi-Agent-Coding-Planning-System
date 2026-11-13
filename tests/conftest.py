"""
Pytest configuration and shared fixtures for DSA AutoGen test suite.
"""

import os
import shutil
import tempfile
from pathlib import Path
import pytest

from dsa_autogen.execution.compiler import CppCompiler
from dsa_autogen.execution.runner_python import PythonRunner
from dsa_autogen.execution.runner_cpp import CppRunner
from dsa_autogen.execution.autogen_executor import MultiLangCodeExecutor


@pytest.fixture(scope="session")
def cpp_compiler():
    try:
        return CppCompiler()
    except Exception as e:
        pytest.skip(f"No C++ compiler available: {e}")


@pytest.fixture
def temp_workspace():
    tmp_dir = Path(tempfile.mkdtemp(prefix="test_dsa_ws_"))
    yield tmp_dir
    shutil.rmtree(tmp_dir, ignore_errors=True)


@pytest.fixture
def python_runner(temp_workspace):
    return PythonRunner(workspace_dir=temp_workspace)


@pytest.fixture
def cpp_runner(temp_workspace, cpp_compiler):
    return CppRunner(compiler=cpp_compiler, workspace_dir=temp_workspace)


@pytest.fixture
def autogen_executor(temp_workspace):
    return MultiLangCodeExecutor(workspace_dir=temp_workspace, timeout_sec=6.0)
