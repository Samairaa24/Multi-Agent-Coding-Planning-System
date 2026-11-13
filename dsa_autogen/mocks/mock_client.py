"""
Mock and Replay LLM Clients for offline testing and deterministic demonstration
of the Self-Healing Execution Loop without requiring API keys.
"""

from __future__ import annotations

from typing import List, Optional, Sequence
from autogen_ext.models.replay import ReplayChatCompletionClient
from autogen_core.models import ModelInfo, ModelFamily

from dsa_autogen.models import Language


def get_mock_planner_response(problem_title: str) -> str:
    return f"""### 1. Problem Classification & Algorithmic Paradigm
Problem: {problem_title}
Paradigm: Hash Map Lookup / Two-Pointer State Optimization
Core Invariant: We maintain a mapping or pointer state to achieve optimal linear time complexity O(N).

### 2. Optimal Complexity Guarantees
- Theoretical Target Time Complexity: O(N) single-pass.
- Theoretical Target Auxiliary Space Complexity: O(N) or O(1).
- Brute force O(N^2) pairwise checking is sub-optimal and will encounter TLE on large constraints.

### 3. Edge Cases & Corner Conditions
- Empty array or minimum constraint size (N = 2 for pairs).
- Negative numbers and zero values.
- Duplicate values present in the input.
- Large scale inputs (10^5 elements) requiring O(N) complexity.

### 4. Step-by-Step Implementation Blueprint
1. Validate input bounds.
2. Maintain lookup structure.
3. Compute complement/condition at each step.
4. Return the result when found.

### 5. Verification Test Suite Specification
- Test 1 (Nominal): Standard positive numbers.
- Test 2 (Duplicates): Array with duplicate target elements.
- Test 3 (Negatives): Negative values included.
- Test 4 (Large / Scale): Elements at opposite ends of array.
"""


def get_mock_buggy_python_code() -> str:
    """Intentionally returns code with an off-by-one / missed negative number bug to trigger self-healing."""
    return '''```python
from typing import List

class Solution:
    def twoSum(self, nums: List[int], target: int) -> List[int]:
        # BUG: Only works for positive numbers, breaks on negative numbers!
        seen = {}
        for i, x in enumerate(nums):
            if x < 0:
                # Bug injected: incorrectly skips negative numbers
                continue
            diff = target - x
            if diff in seen:
                return [seen[diff], i]
            seen[x] = i
        return []

def run_tests():
    sol = Solution()
    
    # Test 1: Standard
    r1 = sol.twoSum([2, 7, 11, 15], 9)
    assert r1 == [0, 1], f"Test 1 failed: got {r1}"
    print("[TEST 1] PASS: Standard case")
    
    # Test 2: Duplicates
    r2 = sol.twoSum([3, 3], 6)
    assert r2 == [0, 1], f"Test 2 failed: got {r2}"
    print("[TEST 2] PASS: Duplicate elements")
    
    # Test 3: Negative numbers (WILL FAIL HERE)
    r3 = sol.twoSum([-3, 4, 3, 90], 0)
    assert r3 == [0, 2], f"Test 3 failed: got {r3}"
    print("[TEST 3] PASS: Negative numbers")
    
    print("ALL TESTS PASSED")

if __name__ == "__main__":
    run_tests()
```'''


def get_mock_fixed_python_code() -> str:
    """Corrected Python implementation that passes all test cases."""
    return '''```python
from typing import List

class Solution:
    def twoSum(self, nums: List[int], target: int) -> List[int]:
        seen = {}
        for i, x in enumerate(nums):
            diff = target - x
            if diff in seen:
                return [seen[diff], i]
            seen[x] = i
        return []

def run_tests():
    sol = Solution()
    
    # Test 1: Standard
    r1 = sol.twoSum([2, 7, 11, 15], 9)
    assert r1 == [0, 1], f"Test 1 failed: got {r1}"
    print("[TEST 1] PASS: Standard case")
    
    # Test 2: Duplicates
    r2 = sol.twoSum([3, 3], 6)
    assert r2 == [0, 1], f"Test 2 failed: got {r2}"
    print("[TEST 2] PASS: Duplicate elements")
    
    # Test 3: Negative numbers
    r3 = sol.twoSum([-3, 4, 3, 90], 0)
    assert r3 == [0, 2], f"Test 3 failed: got {r3}"
    print("[TEST 3] PASS: Negative numbers")
    
    # Test 4: Larger values
    r4 = sol.twoSum([1000000, 500, -1000000], 0)
    assert r4 == [0, 2], f"Test 4 failed: got {r4}"
    print("[TEST 4] PASS: Large magnitude numbers")

    print("ALL TESTS PASSED")

if __name__ == "__main__":
    run_tests()
```'''


def get_mock_buggy_cpp_code() -> str:
    """Intentionally returns C++ code with a compilation syntax error to trigger self-healing."""
    return '''```cpp
#include <iostream>
#include <vector>
#include <unordered_map>
#include <cassert>

class Solution {
public:
    std::vector<int> twoSum(std::vector<int>& nums, int target) {
        std::unordered_map<int, int> seen;
        for (int i = 0; i < (int)nums.size(); ++i) {
            int diff = target - nums[i];
            if (seen.find(diff) != seen.end()) {
                return {seen[diff], i};
            }
            seen[nums[i]] = i;
        }
        return {};
    }
} // BUG: Missing semicolon after class definition!

int main() {
    Solution sol;
    std::vector<int> t1 = {2, 7, 11, 15};
    auto r1 = sol.twoSum(t1, 9);
    assert(r1.size() == 2 && r1[0] == 0 && r1[1] == 1);
    std::cout << "[TEST 1] PASS: Standard case" << std::endl;

    std::vector<int> t2 = {3, 3};
    auto r2 = sol.twoSum(t2, 6);
    assert(r2.size() == 2 && r2[0] == 0 && r2[1] == 1);
    std::cout << "[TEST 2] PASS: Duplicate elements" << std::endl;

    std::vector<int> t3 = {-1, -2, -3, -4, -5};
    auto r3 = sol.twoSum(t3, -8);
    assert(r3.size() == 2 && r3[0] == 2 && r3[1] == 4);
    std::cout << "[TEST 3] PASS: Negative numbers" << std::endl;

    std::cout << "ALL TESTS PASSED" << std::endl;
    return 0;
}
```'''


def get_mock_fixed_cpp_code() -> str:
    """Corrected C++ implementation that compiles and passes all test cases."""
    return '''```cpp
#include <iostream>
#include <vector>
#include <unordered_map>
#include <cassert>

class Solution {
public:
    std::vector<int> twoSum(std::vector<int>& nums, int target) {
        std::unordered_map<int, int> seen;
        for (int i = 0; i < (int)nums.size(); ++i) {
            int diff = target - nums[i];
            if (seen.find(diff) != seen.end()) {
                return {seen[diff], i};
            }
            seen[nums[i]] = i;
        }
        return {};
    }
};

int main() {
    Solution sol;
    std::vector<int> t1 = {2, 7, 11, 15};
    auto r1 = sol.twoSum(t1, 9);
    assert(r1.size() == 2 && r1[0] == 0 && r1[1] == 1);
    std::cout << "[TEST 1] PASS: Standard case" << std::endl;

    std::vector<int> t2 = {3, 3};
    auto r2 = sol.twoSum(t2, 6);
    assert(r2.size() == 2 && r2[0] == 0 && r2[1] == 1);
    std::cout << "[TEST 2] PASS: Duplicate elements" << std::endl;

    std::vector<int> t3 = {-1, -2, -3, -4, -5};
    auto r3 = sol.twoSum(t3, -8);
    assert(r3.size() == 2 && r3[0] == 2 && r3[1] == 4);
    std::cout << "[TEST 3] PASS: Negative numbers" << std::endl;

    std::cout << "ALL TESTS PASSED" << std::endl;
    return 0;
}
```'''


def create_mock_client(language: Language, problem_title: str = "Two Sum") -> ReplayChatCompletionClient:
    """Creates a ReplayChatCompletionClient pre-loaded with Planner -> Buggy Coder -> Fixed Coder responses."""
    plan = get_mock_planner_response(problem_title)
    if language == Language.PYTHON:
        buggy_code = get_mock_buggy_python_code()
        fixed_code = get_mock_fixed_python_code()
    else:
        buggy_code = get_mock_buggy_cpp_code()
        fixed_code = get_mock_fixed_cpp_code()

    # Sequence of model turns:
    # 1. Planner response
    # 2. Coder response 1 (contains bug)
    # 3. Coder response 2 (healed, fixed code)
    completions = [plan, buggy_code, fixed_code]

    model_info = ModelInfo(
        vision=False,
        function_calling=False,
        json_output=False,
        family=ModelFamily.UNKNOWN,
        structured_output=False,
    )
    return ReplayChatCompletionClient(chat_completions=completions, model_info=model_info)

