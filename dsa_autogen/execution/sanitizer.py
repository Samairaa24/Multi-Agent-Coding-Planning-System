"""
Code extraction, language normalization, and test output parsing utilities.
"""

from __future__ import annotations

import re
from typing import List, Optional, Tuple
from dsa_autogen.models import ExecutionStatus, Language


# Regex to extract markdown fenced code blocks with language indicator
CODE_BLOCK_PATTERN = re.compile(r"```([a-zA-Z0-9_\+\-\#]*)\s*\n([\s\S]*?)\n```", re.MULTILINE)

# Test result parsing patterns
TEST_PASS_PATTERN = re.compile(r"\[(?:TEST|CASE)?\s*\d*\]?\s*PASS(?:ED)?|TEST_PASSED|ALL TESTS PASSED", re.IGNORECASE)
TEST_FAIL_PATTERN = re.compile(r"\[(?:TEST|CASE)?\s*\d*\]?\s*FAIL(?:ED)?|TEST_FAILED|AssertionError|assert\s+failed", re.IGNORECASE)


def extract_code_blocks(text: str, default_language: Optional[Language] = None) -> List[Tuple[Language, str]]:
    """
    Extracts all code blocks from text with their mapped language.
    If no fenced blocks exist but text contains code-like structure, returns (default_language, text).
    """
    matches = CODE_BLOCK_PATTERN.findall(text)
    results: List[Tuple[Language, str]] = []

    for lang_tag, code_body in matches:
        lang_str = lang_tag.strip().lower()
        try:
            lang = Language.from_str(lang_str)
            results.append((lang, code_body.strip()))
        except ValueError:
            # Fall back to default if provided
            if default_language:
                results.append((default_language, code_body.strip()))

    if not results and default_language and ("def " in text or "#include" in text or "int main" in text):
        results.append((default_language, text.strip()))

    return results


def parse_test_results(stdout: str, stderr: str, exit_code: int) -> Tuple[ExecutionStatus, int, int, Optional[str]]:
    """
    Analyzes stdout, stderr, and exit_code to determine:
    (ExecutionStatus, passed_tests, total_tests, error_message)
    """
    combined = f"{stdout}\n{stderr}"

    # Count passes and fails first
    pass_matches = len(re.findall(r"(?:\[PASS\]|PASS:|Test\s+\d+:\s+PASS|PASSED)", combined, re.IGNORECASE))
    fail_matches = len(re.findall(r"(?:\[FAIL\]|FAIL:|Test\s+\d+:\s+FAIL|FAILED|AssertionError)", combined, re.IGNORECASE))

    # Check for explicit summary lines like: "Tests: 5 passed, 0 failed"
    summary_match = re.search(r"(\d+)\s+passed,\s+(\d+)\s+failed", combined, re.IGNORECASE)
    if summary_match:
        pass_matches = int(summary_match.group(1))
        fail_matches = int(summary_match.group(2))

    total = pass_matches + fail_matches

    # Check for non-zero exit code failure classifications
    if exit_code != 0:
        if "AssertionError" in combined or fail_matches > 0:
            status = ExecutionStatus.TEST_FAILURE
            error_msg = _extract_core_error(combined) or f"{fail_matches} test assertion(s) failed."
            return status, pass_matches, total, error_msg

        if "Segmentation fault" in combined or "core dumped" in combined or "SIGSEGV" in combined or exit_code in (-11, 139):
            status = ExecutionStatus.RUNTIME_ERROR
            error_msg = "Segmentation Fault (SIGSEGV): Out of bounds access or null pointer dereference."
            return status, 0, 0, error_msg

        if "std::out_of_range" in combined:
            status = ExecutionStatus.RUNTIME_ERROR
            error_msg = "Runtime Error: std::out_of_range exception (vector/array index out of bounds)."
            return status, 0, 0, error_msg

        if "std::bad_alloc" in combined:
            status = ExecutionStatus.RUNTIME_ERROR
            error_msg = "Runtime Error: std::bad_alloc (Out of memory)."
            return status, 0, 0, error_msg

        if "SyntaxError" in combined or ": error:" in combined.lower() or "fatal error:" in combined.lower():
            status = ExecutionStatus.COMPILE_ERROR
            error_msg = _extract_core_error(combined)
            return status, 0, 0, error_msg

    if exit_code == 0:
        if fail_matches > 0:
            status = ExecutionStatus.TEST_FAILURE
            error_msg = f"{fail_matches} test case(s) failed."
        elif "ALL TESTS PASSED" in combined.upper() or pass_matches > 0:
            status = ExecutionStatus.SUCCESS
            error_msg = None
        else:
            # If exit code 0 and no explicit failure found
            status = ExecutionStatus.SUCCESS
            error_msg = None
    else:
        # Non-zero exit
        if fail_matches > 0 or "AssertionError" in combined:
            status = ExecutionStatus.TEST_FAILURE
            error_msg = _extract_core_error(combined) or f"{fail_matches} assertion(s) failed."
        else:
            status = ExecutionStatus.RUNTIME_ERROR
            error_msg = _extract_core_error(combined) or f"Process exited with non-zero code {exit_code}."

    return status, pass_matches, total, error_msg


def _extract_core_error(text: str) -> Optional[str]:
    """Extracts the most relevant error lines from output trace."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    relevant = []
    for line in lines:
        if any(keyword in line for keyword in ["Error:", "error:", "Exception:", "fatal:", "assert", "AssertionError"]):
            relevant.append(line)

    if relevant:
        return "\n".join(relevant[:5])
    return lines[-1] if lines else None
