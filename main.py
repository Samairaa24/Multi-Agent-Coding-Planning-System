#!/usr/bin/env python3
"""
DSA AutoGen CLI - Multi-Agent Self-Healing Execution System for Python and C++ DSA Problems.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from dsa_autogen.config import get_settings
from dsa_autogen.models import Language, ExecutionStatus
from dsa_autogen.problems import get_problem, list_problems
from dsa_autogen.mocks.mock_client import create_mock_client
from dsa_autogen.orchestration.loop import SelfHealingOrchestrator
from dsa_autogen.orchestration.group_chat import create_dsa_group_chat
from dsa_autogen.execution.compiler import CppCompiler


def print_banner(problem_title: str, language: Language, mock_mode: bool):
    print("=" * 70)
    print("       Microsoft AutoGen - Self-Healing Multi-Agent DSA Solver        ")
    print("=" * 70)
    print(f" Target Problem : {problem_title}")
    print(f" Target Language: {language.display_name}")
    print(f" Execution Mode : {'Deterministic MOCK (Offline)' if mock_mode else 'Live LLM'}")

    try:
        compiler = CppCompiler()
        print(f" C++ Compiler   : {compiler.get_compiler_version()}")
    except Exception as e:
        print(f" C++ Compiler   : [Notice] {e}")

    print("=" * 70)
    print()


def make_cli_event_logger():
    """Returns a callback to log loop events cleanly to stdout."""
    def log_event(event_type: str, message: str) -> None:
        prefix_map = {
            "PLANNING_START": "[PLANNER]    ",
            "PLANNING_COMPLETE": "[PLANNER]    Plan generated:\n",
            "CODING_START": "[CODER]      ",
            "EXECUTION_START": "[EXECUTOR]   ",
            "EXECUTION_SUCCESS": "[SUCCESS]    ",
            "HEALING_TRIGGERED": "[SELF-HEAL]  ",
            "HEALING_PATCH_GENERATED": "[CODER]      ",
            "MAX_RETRIES_REACHED": "[FAILED]     ",
        }
        prefix = prefix_map.get(event_type, f"[{event_type}] ")
        if event_type == "PLANNING_COMPLETE":
            # Indent first few lines of plan
            lines = message.strip().splitlines()
            preview = "\n".join(f"    | {l}" for l in lines[:10])
            if len(lines) > 10:
                preview += f"\n    | ... ({len(lines) - 10} more lines)"
            print(f"{prefix}{preview}\n")
        elif event_type in ("EXECUTION_SUCCESS", "HEALING_TRIGGERED", "MAX_RETRIES_REACHED"):
            print(f"\n{prefix}{message}\n")
        else:
            print(f"{prefix}{message}")

    return log_event


async def run_groupchat_mode(problem, language: Language, model_client):
    from autogen_agentchat.messages import TextMessage

    print(f"\n[*] Starting AutoGen 0.4 RoundRobinGroupChat Team for '{problem.title}'...")
    team = create_dsa_group_chat(model_client, language)

    initial_prompt = (
        f"Problem: {problem.title}\n\n"
        f"Description:\n{problem.description}\n\n"
        f"Constraints:\n" + "\n".join(f"- {c}" for c in problem.constraints) + "\n\n"
        f"Planner: Analyze algorithm and edge cases.\n"
        f"Coder: Write {language.display_name} solution with automated test suite.\n"
        f"Executor: Run the code and report output.\n"
        f"When all tests pass, ensure 'ALL TESTS PASSED' is printed."
    )

    async for message in team.run_stream(task=initial_prompt):
        sender = getattr(message, "source", "System")
        content = getattr(message, "content", str(message))
        print(f"\n--- [{sender}] ---\n{content}\n")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Microsoft AutoGen Multi-Agent Self-Healing DSA Solver (Python & C++)"
    )
    parser.add_argument(
        "--problem", "-p",
        type=str,
        default="two_sum",
        help="Problem ID from library (e.g., 'two_sum', 'trapping_rain_water', 'longest_substring', 'subarray_sum_k')",
    )
    parser.add_argument(
        "--language", "-l",
        type=str,
        default="python",
        choices=["python", "cpp", "c++"],
        help="Target programming language (python or cpp)",
    )
    parser.add_argument(
        "--mock", "-m",
        action="store_true",
        help="Run in offline mock mode (deterministic self-healing demonstration, no API key required)",
    )
    parser.add_argument(
        "--max-retries", "-r",
        type=int,
        default=3,
        help="Maximum self-healing retries on failure (default: 3)",
    )
    parser.add_argument(
        "--timeout", "-t",
        type=float,
        default=8.0,
        help="Execution timeout per run in seconds (default: 8.0)",
    )
    parser.add_argument(
        "--mode",
        choices=["loop", "groupchat"],
        default="loop",
        help="Execution mode: 'loop' (self-healing orchestrator with telemetry) or 'groupchat' (AutoGen RoundRobin team)",
    )
    parser.add_argument(
        "--list-problems",
        action="store_true",
        help="List all benchmark problems in the library",
    )
    return parser


async def main_async(args: argparse.Namespace):
    # Resolve language and problem
    language = Language.from_str(args.language)
    problem = get_problem(args.problem)
    if not problem:
        print(f"Error: Problem '{args.problem}' not found. Use --list-problems to view library.")
        sys.exit(1)

    print_banner(problem.title, language, args.mock)

    # Initialize model client
    settings = get_settings()
    if args.mock:
        model_client = create_mock_client(language=language, problem_title=problem.title)
    else:
        api_key = settings.api_key
        if not api_key:
            print("[Warning] OPENAI_API_KEY environment variable is not set.")
            print("Tip: Run with --mock flag for offline deterministic self-healing testing,")
            print("or set OPENAI_API_KEY in your environment / .env file.")
            sys.exit(1)

        from autogen_ext.models.openai import OpenAIChatCompletionClient
        client_kwargs = {
            "model": settings.model_name,
            "api_key": api_key,
            "temperature": settings.temperature,
        }
        if settings.base_url:
            client_kwargs["base_url"] = settings.base_url
        model_client = OpenAIChatCompletionClient(**client_kwargs)

    if args.mode == "groupchat":
        await run_groupchat_mode(problem, language, model_client)
        return

    # Run Self-Healing Orchestration Loop
    orchestrator = SelfHealingOrchestrator(
        model_client=model_client,
        max_retries=args.max_retries,
        timeout_sec=args.timeout,
    )

    logger = make_cli_event_logger()
    report = await orchestrator.run(
        problem=problem,
        language=language,
        on_event=logger,
    )

    # Print Final Verification Report
    print("=" * 70)
    print("                      FINAL EXECUTION REPORT                          ")
    print("=" * 70)
    print(f" Status          : {report.final_status.value}")
    print(f" Total Rounds    : {report.total_iterations} iteration(s)")
    print(f" Total Duration  : {report.total_time_seconds:.2f} seconds")
    print(f" Self-Healed     : {'YES (Bugs diagnosed and fixed)' if report.healed else ('YES (Passed on first try)' if report.passed_on_first_try else 'NO')}")
    print("-" * 70)

    if report.final_status == ExecutionStatus.SUCCESS:
        print("\nVerified Solution Code:\n")
        print(report.final_code)
        print("\n" + "=" * 70)
        print("[SUCCESS] Solution verified and ready for deployment!")
        sys.exit(0)
    else:
        print("\n[FAILURE] Could not heal the solution within retry budget.")
        sys.exit(1)


def main():
    parser = build_parser()
    args = parser.parse_args()

    if args.list_problems:
        print("\nAvailable DSA Benchmark Problems:")
        for prob in list_problems():
            print(f"  * {prob.id:<25} - {prob.title} (Target: {prob.target_time_complexity}, {prob.target_space_complexity})")
        return

    try:
        asyncio.run(main_async(args))
    except KeyboardInterrupt:
        print("\n[!] Execution interrupted by user.")
        sys.exit(130)


if __name__ == "__main__":
    main()
