#!/usr/bin/env python3
"""
Test Runner for SmartCanopy AI

This script runs the test suite with various options.

Usage:
    python scripts/run_tests.py              # Run all tests
    python scripts/run_tests.py --unit       # Run only unit tests
    python scripts/run_tests.py --fast       # Skip slow tests
    python scripts/run_tests.py --coverage   # Run with coverage report
"""

import sys
import subprocess
import argparse
from pathlib import Path

# Change to project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def run_tests(args):
    """Run pytest with specified options"""

    pytest_args = ["pytest"]

    # Test selection
    if args.unit:
        pytest_args.extend(["-m", "unit"])
        print("🧪 Running UNIT tests only\n")
    elif args.integration:
        pytest_args.extend(["-m", "integration"])
        print("🔗 Running INTEGRATION tests only\n")
    elif args.e2e:
        pytest_args.extend(["-m", "e2e"])
        print("🎬 Running END-TO-END tests only\n")
    elif args.performance:
        pytest_args.extend(["-m", "performance"])
        print("⚡ Running PERFORMANCE tests only\n")
    else:
        print("🧪 Running ALL tests\n")

    # Speed options
    if args.fast:
        pytest_args.extend(["-m", "not slow"])
        print("⏩ Skipping slow tests\n")

    # Coverage
    if args.coverage:
        pytest_args.extend([
            "--cov=agent",
            "--cov=api",
            "--cov-report=html",
            "--cov-report=term-missing"
        ])
        print("📊 Coverage reporting enabled\n")

    # Verbosity
    if args.verbose:
        pytest_args.append("-vv")
    elif args.quiet:
        pytest_args.append("-q")

    # Specific test file
    if args.file:
        pytest_args.append(f"tests/{args.file}")
        print(f"📁 Running tests from: {args.file}\n")

    # Specific test function
    if args.test:
        pytest_args.extend(["-k", args.test])
        print(f"🎯 Running tests matching: {args.test}\n")

    # Stop on first failure
    if args.exitfirst:
        pytest_args.append("-x")

    # Show local variables on failure
    if args.showlocals:
        pytest_args.append("-l")

    # Parallel execution
    if args.parallel:
        pytest_args.extend(["-n", str(args.parallel)])
        print(f"⚡ Running {args.parallel} tests in parallel\n")

    print("="*80)
    print(f"Running: {' '.join(pytest_args)}")
    print("="*80 + "\n")

    # Run pytest
    result = subprocess.run(pytest_args)

    if args.coverage and result.returncode == 0:
        print("\n" + "="*80)
        print("📊 Coverage report generated: htmlcov/index.html")
        print("="*80)

    return result.returncode


def main():
    parser = argparse.ArgumentParser(
        description="Run SmartCanopy AI test suite",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all tests
  python scripts/run_tests.py

  # Run only unit tests
  python scripts/run_tests.py --unit

  # Run with coverage report
  python scripts/run_tests.py --coverage

  # Run specific test file
  python scripts/run_tests.py --file test_agent.py

  # Run specific test function
  python scripts/run_tests.py --test test_species_recommender

  # Run fast tests only (skip slow ones)
  python scripts/run_tests.py --fast

  # Run tests in parallel
  python scripts/run_tests.py --parallel 4
        """
    )

    # Test selection
    test_group = parser.add_mutually_exclusive_group()
    test_group.add_argument(
        "--unit",
        action="store_true",
        help="Run only unit tests"
    )
    test_group.add_argument(
        "--integration",
        action="store_true",
        help="Run only integration tests"
    )
    test_group.add_argument(
        "--e2e",
        action="store_true",
        help="Run only end-to-end tests"
    )
    test_group.add_argument(
        "--performance",
        action="store_true",
        help="Run only performance tests"
    )

    # Options
    parser.add_argument(
        "--fast",
        action="store_true",
        help="Skip slow tests"
    )
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Generate coverage report"
    )
    parser.add_argument(
        "--file",
        type=str,
        help="Run specific test file (e.g., test_agent.py)"
    )
    parser.add_argument(
        "--test",
        type=str,
        help="Run tests matching pattern (e.g., test_species)"
    )
    parser.add_argument(
        "--parallel",
        type=int,
        metavar="N",
        help="Run N tests in parallel (requires pytest-xdist)"
    )
    parser.add_argument(
        "--exitfirst", "-x",
        action="store_true",
        help="Stop on first failure"
    )
    parser.add_argument(
        "--showlocals", "-l",
        action="store_true",
        help="Show local variables on failure"
    )

    # Verbosity
    verbosity_group = parser.add_mutually_exclusive_group()
    verbosity_group.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    verbosity_group.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Quiet output"
    )

    args = parser.parse_args()

    sys.exit(run_tests(args))


if __name__ == "__main__":
    main()
