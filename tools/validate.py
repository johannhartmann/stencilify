#!/usr/bin/env python3
"""
Validation tool for stencilify project.

Runs the standard validation sequence:
1. ruff format --check
2. ruff check
3. mypy
4. pytest -q

Exits with non-zero code if any check fails.
"""

import subprocess
import sys


def run_check(name: str, command: list[str]) -> bool:
    """Run a validation check and return True if successful."""
    print(f"\n{'=' * 60}")
    print(f"Running: {name}")
    print(f"Command: {' '.join(command)}")
    print('=' * 60)

    result = subprocess.run(command, capture_output=False)

    if result.returncode == 0:
        print(f"✓ {name} PASSED")
        return True
    else:
        print(f"✗ {name} FAILED (exit code {result.returncode})")
        return False


def main() -> int:
    """Run all validation checks."""
    print("Starting validation sequence...")

    checks = [
        ("ruff format", ["uv", "run", "ruff", "format", "--check", "."]),
        ("ruff check", ["uv", "run", "ruff", "check", "."]),
        ("mypy", ["uv", "run", "mypy", "."]),
        ("pytest", ["uv", "run", "pytest", "-q"]),
    ]

    results = []
    for name, command in checks:
        results.append(run_check(name, command))

    print(f"\n{'=' * 60}")
    print("Validation Summary")
    print('=' * 60)

    for (name, _), passed in zip(checks, results):
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {name}")

    all_passed = all(results)
    print(f"\n{'=' * 60}")
    if all_passed:
        print("All validation checks PASSED ✓")
        print('=' * 60)
        return 0
    else:
        print("Some validation checks FAILED ✗")
        print('=' * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
