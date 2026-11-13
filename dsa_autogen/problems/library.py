"""
Benchmark library of standard DSA problems for Python and C++.
"""

from __future__ import annotations

from typing import Dict, List, Optional
from dsa_autogen.models import DSAProblem, TestCase, Language


PROBLEMS_CATALOG: Dict[str, DSAProblem] = {
    "two_sum": DSAProblem(
        id="two_sum",
        title="Two Sum",
        description=(
            "Given an array of integers nums and an integer target, return indices of the two numbers such that they add up to target.\n"
            "You may assume that each input would have exactly one solution, and you may not use the same element twice.\n"
            "You can return the answer in any order."
        ),
        constraints=[
            "2 <= nums.length <= 10^4",
            "-10^9 <= nums[i] <= 10^9",
            "-10^9 <= target <= 10^9",
            "Only one valid answer exists.",
        ],
        examples=[
            {"input": "nums = [2,7,11,15], target = 9", "output": "[0,1]"},
            {"input": "nums = [3,2,4], target = 6", "output": "[1,2]"},
            {"input": "nums = [3,3], target = 6", "output": "[0,1]"},
        ],
        test_cases=[
            TestCase(name="Standard Test", input_repr="nums=[2,7,11,15], target=9", expected_output="[0,1]"),
            TestCase(name="Offset Indices", input_repr="nums=[3,2,4], target=6", expected_output="[1,2]"),
            TestCase(name="Duplicates", input_repr="nums=[3,3], target=6", expected_output="[0,1]"),
            TestCase(name="Negative Numbers", input_repr="nums=[-3,4,3,90], target=0", expected_output="[0,2]"),
        ],
        target_time_complexity="O(N)",
        target_space_complexity="O(N)",
    ),

    "trapping_rain_water": DSAProblem(
        id="trapping_rain_water",
        title="Trapping Rain Water",
        description=(
            "Given n non-negative integers representing an elevation map where the width of each bar is 1, "
            "compute how much water it can trap after raining."
        ),
        constraints=[
            "n == height.length",
            "1 <= n <= 2 * 10^4",
            "0 <= height[i] <= 10^5",
        ],
        examples=[
            {"input": "height = [0,1,0,2,1,0,1,3,2,1,2,1]", "output": "6"},
            {"input": "height = [4,2,0,3,2,5]", "output": "9"},
        ],
        test_cases=[
            TestCase(name="Standard Complex Map", input_repr="[0,1,0,2,1,0,1,3,2,1,2,1]", expected_output="6"),
            TestCase(name="Valley Basin", input_repr="[4,2,0,3,2,5]", expected_output="9"),
            TestCase(name="Flat Array", input_repr="[3,3,3,3]", expected_output="0"),
            TestCase(name="Single Bar", input_repr="[5]", expected_output="0"),
            TestCase(name="Strictly Ascending", input_repr="[1,2,3,4,5]", expected_output="0"),
        ],
        target_time_complexity="O(N)",
        target_space_complexity="O(1)",
    ),

    "longest_substring": DSAProblem(
        id="longest_substring",
        title="Longest Substring Without Repeating Characters",
        description=(
            "Given a string s, find the length of the longest substring without repeating characters."
        ),
        constraints=[
            "0 <= s.length <= 5 * 10^4",
            "s consists of English letters, digits, symbols and spaces.",
        ],
        examples=[
            {"input": "s = 'abcabcbb'", "output": "3"},
            {"input": "s = 'bbbbb'", "output": "1"},
            {"input": "s = 'pwwkew'", "output": "3"},
        ],
        test_cases=[
            TestCase(name="Standard Repeating", input_repr="'abcabcbb'", expected_output="3"),
            TestCase(name="All Identical", input_repr="'bbbbb'", expected_output="1"),
            TestCase(name="Internal Repetition", input_repr="'pwwkew'", expected_output="3"),
            TestCase(name="Empty String", input_repr="''", expected_output="0"),
            TestCase(name="All Unique", input_repr="'abcdef'", expected_output="6"),
        ],
        target_time_complexity="O(N)",
        target_space_complexity="O(min(N, M))",
    ),

    "subarray_sum_k": DSAProblem(
        id="subarray_sum_k",
        title="Subarray Sum Equals K",
        description=(
            "Given an array of integers nums and an integer k, return the total number of subarrays whose sum equals to k.\n"
            "A subarray is a contiguous non-empty sequence of elements within an array."
        ),
        constraints=[
            "1 <= nums.length <= 2 * 10^4",
            "-1000 <= nums[i] <= 1000",
            "-10^7 <= k <= 10^7",
        ],
        examples=[
            {"input": "nums = [1,1,1], k = 2", "output": "2"},
            {"input": "nums = [1,2,3], k = 3", "output": "2"},
        ],
        test_cases=[
            TestCase(name="Simple Sum", input_repr="nums=[1,1,1], k=2", expected_output="2"),
            TestCase(name="Multiple Overlaps", input_repr="nums=[1,2,3], k=3", expected_output="2"),
            TestCase(name="With Negatives", input_repr="nums=[1,-1,0], k=0", expected_output="3"),
            TestCase(name="Single Match", input_repr="nums=[5], k=5", expected_output="1"),
            TestCase(name="No Match", input_repr="nums=[1,2,3], k=7", expected_output="0"),
        ],
        target_time_complexity="O(N)",
        target_space_complexity="O(N)",
    ),
}


def get_problem(problem_id: str) -> Optional[DSAProblem]:
    """Retrieve problem from library by ID."""
    return PROBLEMS_CATALOG.get(problem_id.lower())


def list_problems() -> List[DSAProblem]:
    """Return all available problems in the catalog."""
    return list(PROBLEMS_CATALOG.values())

