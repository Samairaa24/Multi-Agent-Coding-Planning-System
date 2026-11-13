"""
Tests for PythonRunner and CppRunner.
"""

import pytest
from dsa_autogen.models import ExecutionStatus, Language


@pytest.mark.asyncio
async def test_python_runner_success(python_runner):
    code = """
def run():
    print("[TEST 1] PASS: Simple check")
    print("ALL TESTS PASSED")

if __name__ == "__main__":
    run()
"""
    res = await python_runner.run(code, timeout_sec=5.0)
    assert res.is_success
    assert res.status == ExecutionStatus.SUCCESS
    assert res.exit_code == 0
    assert "ALL TESTS PASSED" in res.stdout


@pytest.mark.asyncio
async def test_python_runner_assertion_failure(python_runner):
    code = """
if __name__ == "__main__":
    print("[TEST 1] PASS")
    assert 1 == 2, "1 != 2 test failed"
"""
    res = await python_runner.run(code, timeout_sec=5.0)
    assert not res.is_success
    assert res.status == ExecutionStatus.TEST_FAILURE
    assert res.exit_code != 0
    assert "AssertionError" in res.stderr or "1 != 2" in res.stderr


@pytest.mark.asyncio
async def test_python_runner_timeout(python_runner):
    code = """
import time
if __name__ == "__main__":
    while True:
        time.sleep(0.1)
"""
    res = await python_runner.run(code, timeout_sec=1.0)
    assert not res.is_success
    assert res.status == ExecutionStatus.TIMEOUT
    assert "Time Limit Exceeded" in (res.error_message or "")


@pytest.mark.asyncio
async def test_cpp_runner_success(cpp_runner):
    code = """
#include <iostream>
int main() {
    std::cout << "[TEST 1] PASS: Basic test" << std::endl;
    std::cout << "ALL TESTS PASSED" << std::endl;
    return 0;
}
"""
    res = await cpp_runner.run(code, timeout_sec=5.0)
    assert res.is_success
    assert res.status == ExecutionStatus.SUCCESS
    assert res.exit_code == 0
    assert "ALL TESTS PASSED" in res.stdout


@pytest.mark.asyncio
async def test_cpp_runner_compile_error(cpp_runner):
    code = """
#include <iostream>
int main() {
    this_is_an_invalid_token();
    return 0;
}
"""
    res = await cpp_runner.run(code, timeout_sec=5.0)
    assert not res.is_success
    assert res.status == ExecutionStatus.COMPILE_ERROR
    assert res.exit_code != 0


@pytest.mark.asyncio
async def test_cpp_runner_runtime_crash(cpp_runner):
    code = """
#include <iostream>
#include <vector>
#include <stdexcept>
int main() {
    try {
        std::vector<int> v = {1, 2};
        std::cout << v.at(10) << std::endl;
    } catch (const std::out_of_range& e) {
        std::cerr << "std::out_of_range: index out of bounds" << std::endl;
        return 1;
    }
    return 0;
}
"""
    res = await cpp_runner.run(code, timeout_sec=5.0)
    assert not res.is_success
    assert res.status in (ExecutionStatus.RUNTIME_ERROR, ExecutionStatus.TEST_FAILURE)
    assert res.exit_code != 0
    assert "std::out_of_range" in res.error_message or "std::out_of_range" in res.stderr
