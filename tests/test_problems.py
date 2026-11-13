"""
Tests for problem library catalog.
"""

from dsa_autogen.problems import get_problem, list_problems


def test_list_problems():
    problems = list_problems()
    assert len(problems) >= 4
    ids = [p.id for p in problems]
    assert "two_sum" in ids
    assert "trapping_rain_water" in ids
    assert "longest_substring" in ids
    assert "subarray_sum_k" in ids


def test_get_problem():
    p = get_problem("two_sum")
    assert p is not None
    assert p.title == "Two Sum"
    assert len(p.test_cases) >= 3
    assert p.target_time_complexity == "O(N)"

