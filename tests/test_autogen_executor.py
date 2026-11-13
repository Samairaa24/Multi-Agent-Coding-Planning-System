"""
Tests for MultiLangCodeExecutor conforming to AutoGen CodeExecutor ABC.
"""

import pytest
from autogen_core import CancellationToken
from autogen_core.code_executor import CodeBlock


@pytest.mark.asyncio
async def test_autogen_executor_python_blocks(autogen_executor):
    code = """
print("[TEST 1] PASS")
print("ALL TESTS PASSED")
"""
    blocks = [CodeBlock(code=code, language="python")]
    res = await autogen_executor.execute_code_blocks(blocks, CancellationToken())
    assert res.exit_code == 0
    assert "ALL TESTS PASSED" in res.output


@pytest.mark.asyncio
async def test_autogen_executor_cpp_blocks(autogen_executor):
    code = """
#include <iostream>
int main() {
    std::cout << "[TEST 1] PASS: C++ block" << std::endl;
    std::cout << "ALL TESTS PASSED" << std::endl;
    return 0;
}
"""
    blocks = [CodeBlock(code=code, language="cpp")]
    res = await autogen_executor.execute_code_blocks(blocks, CancellationToken())
    assert res.exit_code == 0
    assert "ALL TESTS PASSED" in res.output


@pytest.mark.asyncio
async def test_autogen_executor_cancellation(autogen_executor):
    token = CancellationToken()
    token.cancel()
    blocks = [CodeBlock(code="print('hi')", language="python")]
    res = await autogen_executor.execute_code_blocks(blocks, token)
    assert res.exit_code == -1
    assert "cancelled" in res.output.lower()

