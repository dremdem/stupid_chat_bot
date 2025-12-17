"""
Invoke tasks for the Stupid Chat Bot backend.

This file defines common development tasks that can be executed using the `invoke` command.
All tasks should be run from the backend directory with the virtual environment activated.

Usage:
    invoke --list              # Show all available tasks
    invoke test                # Run tests (in Docker)
    invoke lint                # Run linting (locally)
    invoke format              # Format code (locally)
"""

import os
import time

from invoke import task


def ensure_docker_running(c):
    """
    Ensure Docker backend service is running.

    Checks if the backend container is running, and starts it if not.
    Returns True if container is ready, False if failed.
    """
    # Check if container exists and is running
    result = c.run(
        "docker compose ps --status=running -q backend", warn=True, hide=True, echo=False
    )

    if result.stdout.strip():
        return True

    print("Starting Docker services...")
    start_result = c.run("docker compose up -d backend", warn=True, pty=True)

    if start_result.exited != 0:
        print("❌ Failed to start Docker services")
        return False

    # Wait for backend to be ready
    print("Waiting for backend to be ready...")
    for i in range(30):
        health_check = c.run(
            "docker compose exec -T backend python -c 'import app; print(\"ready\")'",
            warn=True,
            hide=True,
            echo=False,
        )
        if health_check.exited == 0:
            print("✅ Backend is ready")
            return True
        time.sleep(1)

    print("❌ Backend failed to become ready within timeout")
    return False


@task
def test(c, verbose=False, coverage=False):
    """
    Run tests using pytest in Docker container.

    Tests run in Docker to ensure consistent environment and avoid
    installing heavy test dependencies locally.

    Args:
        verbose: Run tests in verbose mode (-v)
        coverage: Run tests with coverage report
    """
    # Check if tests directory exists
    if not os.path.exists("tests"):
        print("⚠️  No tests directory found yet.")
        print("Tests will be implemented in Phase 4-5.")
        print("Skipping test execution.")
        return

    # Ensure Docker is running
    if not ensure_docker_running(c):
        return

    cmd = "pytest"

    if verbose:
        cmd += " -v"

    if coverage:
        cmd += " --cov=app --cov-report=html --cov-report=term"

    print(f"Running tests in Docker: {cmd}")
    result = c.run(f"docker compose exec -T backend {cmd}", warn=True, pty=True)

    if result.exited != 0:
        print("\n❌ Tests failed")
    else:
        print("\n✅ All tests passed!")


@task
def lint(c, fix=False):
    """
    Run linting checks using ruff.

    Args:
        fix: Automatically fix linting issues where possible
    """
    cmd = "ruff check ."

    if fix:
        cmd += " --fix"

    print(f"Running: {cmd}")
    result = c.run(cmd, warn=True, pty=True)

    if result.exited != 0:
        print("\n❌ Linting failed. Fix the issues above or run 'invoke lint --fix'")
        return result
    else:
        print("\n✅ Linting passed!")


@task
def format(c, check=False):
    """
    Format code using black.

    Args:
        check: Check if files would be reformatted without making changes
    """
    cmd = "black ."

    if check:
        cmd += " --check"

    print(f"Running: {cmd}")
    result = c.run(cmd, warn=True, pty=True)

    if result.exited != 0 and check:
        print("\n❌ Code formatting check failed. Run 'invoke format' to fix.")
        return result
    elif not check:
        print("\n✅ Code formatted!")


@task
def clean(c):
    """
    Clean up cache files and temporary directories.

    Removes:
        - __pycache__ directories
        - .pyc, .pyo files
        - .pytest_cache
        - .ruff_cache
        - .coverage files
    """
    print("Cleaning cache files...")

    # Remove __pycache__ directories
    c.run("find . -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true")

    # Remove .pyc and .pyo files
    c.run("find . -type f -name '*.pyc' -delete 2>/dev/null || true")
    c.run("find . -type f -name '*.pyo' -delete 2>/dev/null || true")

    # Remove pytest cache
    c.run("rm -rf .pytest_cache", warn=True)

    # Remove ruff cache
    c.run("rm -rf .ruff_cache", warn=True)

    # Remove coverage files
    c.run("rm -f .coverage", warn=True)
    c.run("rm -rf htmlcov", warn=True)

    print("✅ Cleanup complete!")


@task
def check(c):
    """
    Run all checks (format check, lint, and tests).

    - Format and lint run locally (fast)
    - Tests run in Docker (consistent environment)

    This is useful for pre-commit checks or CI/CD.
    """
    print("=" * 60)
    print("Running format check (local)...")
    print("=" * 60)
    format_result = format(c, check=True)

    print("\n" + "=" * 60)
    print("Running linting (local)...")
    print("=" * 60)
    lint_result = lint(c)

    print("\n" + "=" * 60)
    print("Running tests (Docker)...")
    print("=" * 60)
    test_result = test(c)

    # Check if any failed
    failed = False
    if format_result and hasattr(format_result, "exited") and format_result.exited != 0:
        failed = True
    if lint_result and hasattr(lint_result, "exited") and lint_result.exited != 0:
        failed = True
    if test_result and hasattr(test_result, "exited") and test_result.exited != 0:
        failed = True

    if failed:
        print("\n" + "=" * 60)
        print("❌ Some checks failed")
        print("=" * 60)
        return False

    print("\n" + "=" * 60)
    print("✅ All checks passed!")
    print("=" * 60)
    return True


@task
def dev(c):
    """
    Start the development server with auto-reload.

    Runs uvicorn with reload enabled on port 8000.
    """
    print("Starting development server...")
    print("Server will be available at: http://localhost:8000")
    print("API docs at: http://localhost:8000/docs")
    print("\nPress Ctrl+C to stop the server\n")

    c.run("uvicorn app.main:app --reload --host 0.0.0.0 --port 8000", pty=True)


@task
def lock(c, upgrade=False):
    """
    Update the uv.lock file.

    Args:
        upgrade: Upgrade all dependencies to their latest versions
    """
    cmd = "uv lock"

    if upgrade:
        cmd += " --upgrade"
        print("Upgrading all dependencies...")
    else:
        print("Updating lock file...")

    c.run(cmd, pty=True)
    print("✅ Lock file updated!")


@task
def install(c, dev=True):
    """
    Install dependencies using uv.

    Args:
        dev: Install development dependencies (default: True)
    """
    cmd = "uv sync"

    if dev:
        cmd += " --all-extras"
        print("Installing all dependencies (including dev)...")
    else:
        print("Installing production dependencies only...")

    c.run(cmd, pty=True)
    print("✅ Dependencies installed!")


@task
def precommit(c, all_files=False):
    """
    Run pre-commit hooks.

    Args:
        all_files: Run on all files instead of just staged files
    """
    if all_files:
        print("Running pre-commit on all files...")
        c.run("pre-commit run --all-files", pty=True)
    else:
        print("Running pre-commit on staged files...")
        c.run("pre-commit run", pty=True)


@task
def test_local(c, verbose=False, coverage=False):
    """
    Run tests locally (requires dev-test dependencies installed).

    This is useful for debugging tests with IDE integration.
    Most users should use 'invoke test' which runs in Docker.

    Args:
        verbose: Run tests in verbose mode (-v)
        coverage: Run tests with coverage report
    """
    cmd = "pytest"

    if verbose:
        cmd += " -v"

    if coverage:
        cmd += " --cov=app --cov-report=html --cov-report=term"

    print(f"Running locally: {cmd}")
    print("Note: Requires 'uv sync --extra dev-test' to be run first")
    c.run(cmd, pty=True)


@task
def lint_docker(c, fix=False):
    """
    Run linting checks using ruff in Docker container.

    This ensures CI consistency. For local development, use 'invoke lint'.

    Args:
        fix: Automatically fix linting issues where possible
    """
    if not ensure_docker_running(c):
        return

    cmd = "ruff check ."

    if fix:
        cmd += " --fix"

    print(f"Running linting in Docker: {cmd}")
    result = c.run(f"docker compose exec -T backend {cmd}", warn=True, pty=True)

    if result.exited != 0:
        print("\n❌ Linting failed. Fix the issues above or run 'invoke lint-docker --fix'")
        return result
    else:
        print("\n✅ Linting passed!")


@task
def format_docker(c, check=False):
    """
    Format code using black in Docker container.

    This ensures CI consistency. For local development, use 'invoke format'.

    Args:
        check: Check if files would be reformatted without making changes
    """
    if not ensure_docker_running(c):
        return

    cmd = "black ."

    if check:
        cmd += " --check"

    print(f"Running formatting in Docker: {cmd}")
    result = c.run(f"docker compose exec -T backend {cmd}", warn=True, pty=True)

    if result.exited != 0 and check:
        print("\n❌ Code formatting check failed. Run 'invoke format-docker' to fix.")
        return result
    elif not check:
        print("\n✅ Code formatted!")


@task
def ci(c):
    """
    Run complete CI pipeline (format check + lint + tests).

    This task mirrors the GitHub Actions workflow and should pass
    before pushing code. All checks run locally for fast feedback.
    """
    print("=" * 60)
    print("Running CI Pipeline")
    print("=" * 60)

    # Track failures
    failed = []

    # 1. Format check
    print("\n" + "=" * 60)
    print("1/3: Format Check")
    print("=" * 60)
    format_result = c.run("black . --check", warn=True, pty=True)
    if format_result.exited != 0:
        failed.append("Format check")

    # 2. Lint
    print("\n" + "=" * 60)
    print("2/3: Lint")
    print("=" * 60)
    lint_result = c.run("ruff check .", warn=True, pty=True)
    if lint_result.exited != 0:
        failed.append("Lint")

    # 3. Tests (if tests directory exists)
    if os.path.exists("tests"):
        print("\n" + "=" * 60)
        print("3/3: Tests")
        print("=" * 60)
        test(c)
    else:
        print("\n" + "=" * 60)
        print("3/3: Tests - SKIPPED (no tests directory)")
        print("=" * 60)

    # Summary
    print("\n" + "=" * 60)
    if failed:
        print(f"❌ CI Failed: {', '.join(failed)}")
        print("=" * 60)
        return False
    else:
        print("✅ CI Passed")
        print("=" * 60)
        return True
