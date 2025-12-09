"""
Invoke tasks for the Stupid Chat Bot backend.

This file defines common development tasks that can be executed using the `invoke` command.
All tasks should be run from the backend directory with the virtual environment activated.

Usage:
    invoke --list              # Show all available tasks
    invoke test                # Run tests
    invoke lint                # Run linting
    invoke format              # Format code
"""

from invoke import task


@task
def test(c, verbose=False, coverage=False):
    """
    Run tests using pytest.

    Args:
        verbose: Run tests in verbose mode (-v)
        coverage: Run tests with coverage report
    """
    cmd = "pytest"

    if verbose:
        cmd += " -v"

    if coverage:
        cmd += " --cov=app --cov-report=html --cov-report=term"

    print(f"Running: {cmd}")
    c.run(cmd, pty=True)


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

    This is useful for pre-commit checks or CI/CD.
    """
    print("=" * 60)
    print("Running format check...")
    print("=" * 60)
    format(c, check=True)

    print("\n" + "=" * 60)
    print("Running linting...")
    print("=" * 60)
    lint(c)

    print("\n" + "=" * 60)
    print("Running tests...")
    print("=" * 60)
    test(c)

    print("\n" + "=" * 60)
    print("✅ All checks passed!")
    print("=" * 60)


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
