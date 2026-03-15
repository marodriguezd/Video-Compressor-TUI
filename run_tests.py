#!/usr/bin/env python
"""
Test runner script for Video-Slice-TUI.

Usage:
    python run_tests.py              # Run all tests
    python run_tests.py --quick      # Run only unit tests (skip integration)
    python run_tests.py --coverage   # Run with coverage report
    python run_tests.py --verbose    # Run with verbose output
"""

import subprocess
import sys
import os


def run_tests(args=None):
    """Run the test suite."""
    project_root = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_root)

    cmd = [sys.executable, "-m", "pytest"]

    if args:
        cmd.extend(args)
    else:
        # Default: run all tests
        cmd.extend(
            [
                "tests/",
                "-v",
                "--tb=short",
            ]
        )

    print(f"Running: {' '.join(cmd)}")
    print("-" * 50)

    result = subprocess.run(cmd)
    return result.returncode


def run_quick_tests():
    """Run only unit tests (skip slow integration tests)."""
    return run_tests(["tests/test_logic/", "-v", "--tb=short"])


def run_with_coverage():
    """Run tests with coverage report."""
    try:
        import pytest_cov
    except ImportError:
        print("Installing pytest-cov...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pytest-cov"])
        import pytest_cov

    return run_tests(
        [
            "tests/",
            "--cov=src/logic",
            "--cov-report=term-missing",
            "--cov-report=html",
            "-v",
        ]
    )


def check_dependencies():
    """Check if test dependencies are installed."""
    required = ["pytest", "pytest-asyncio"]
    missing = []

    for dep in required:
        try:
            __import__(dep.replace("-", "_"))
        except ImportError:
            missing.append(dep)

    if missing:
        print(f"Missing dependencies: {', '.join(missing)}")
        print("Installing...")
        subprocess.run([sys.executable, "-m", "pip", "install"] + missing)
        return True
    return True


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Test runner for Video-Slice-TUI")
    parser.add_argument("--quick", action="store_true", help="Run only unit tests")
    parser.add_argument("--coverage", action="store_true", help="Run with coverage")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")

    args = parser.parse_args()

    check_dependencies()

    if args.quick:
        print("Running quick tests (unit tests only)...")
        return run_quick_tests()
    elif args.coverage:
        print("Running tests with coverage...")
        return run_with_coverage()
    else:
        return run_tests()


if __name__ == "__main__":
    sys.exit(main())
