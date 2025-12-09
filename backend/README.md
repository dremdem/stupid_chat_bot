# Backend - Stupid Chat Bot

FastAPI backend for the Stupid Chat Bot application.

## Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI application entry point
│   ├── api/              # API route handlers
│   ├── services/         # Business logic and services
│   └── models/           # Data models and schemas
├── requirements.txt      # Python dependencies
├── .env.example         # Environment variable template
├── Dockerfile           # Docker configuration
└── pyproject.toml       # Python project configuration
```

## Setup

### Quick Start (Docker)

The fastest way to get started:
```bash
cd ..
docker compose up --build
```

### Local Development Environment

For running tests, linting, and other service tasks locally (not for production).

#### Prerequisites
- Python 3.12+
- Bash shell (Linux/macOS)

#### Initial Setup

1. Run the setup script:
```bash
./setup_local_env.sh
```

This script will:
- Check if `uv` is installed (and install it if missing)
- Create a virtual environment in `.venv/`
- Install all dependencies (including dev dependencies)
- Verify the installation

2. Activate the environment:
```bash
source ./activate_env.sh
```

Or manually:
```bash
source .venv/bin/activate
```

3. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

#### Running the Development Server

With the environment activated:
```bash
invoke dev
```

Or directly:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API Documentation

When the server is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Endpoints

- `GET /` - Root endpoint
- `GET /health` - Health check endpoint

More endpoints will be added in Phase 2 (WebSocket) and Phase 3 (AI integration).

## Development

### Using Invoke Tasks

The project includes an `invoke` task runner for common development tasks. Make sure your virtual environment is activated first.

#### Available Tasks

List all available tasks:
```bash
invoke --list
```

#### Testing

Run tests:
```bash
invoke test
```

Run tests with verbose output:
```bash
invoke test --verbose
```

Run tests with coverage report:
```bash
invoke test --coverage
```

#### Code Quality

Format code with black:
```bash
invoke format
```

Check formatting without making changes:
```bash
invoke format --check
```

Run linting with ruff:
```bash
invoke lint
```

Auto-fix linting issues:
```bash
invoke lint --fix
```

Run all checks (format, lint, test):
```bash
invoke check
```

#### Maintenance

Clean cache files:
```bash
invoke clean
```

Install/update dependencies:
```bash
invoke install
```

Update lock file:
```bash
invoke lock
```

Upgrade all dependencies:
```bash
invoke lock --upgrade
```

Run pre-commit hooks:
```bash
invoke precommit
```

Run pre-commit on all files:
```bash
invoke precommit --all-files
```

### Manual Commands

If you prefer not to use invoke, you can run commands directly:

#### Code Formatting
```bash
black .
```

#### Linting
```bash
ruff check .
```

#### Testing
```bash
pytest
```

### Dependency Management

#### Adding Dependencies

Production dependency:
```bash
uv add <package-name>
```

Development dependency:
```bash
uv add --dev <package-name>
```

After adding dependencies, update the lock file:
```bash
uv lock
```

#### Updating Dependencies

Update all dependencies:
```bash
uv lock --upgrade
```

Update specific package:
```bash
uv lock --upgrade-package <package-name>
```

### Environment Cleanup

To completely reset your local environment:
```bash
./cleanup_env.sh
```

This will remove:
- Virtual environment (`.venv/`)
- Python cache files (`__pycache__/`, `*.pyc`, `*.pyo`)
- Test cache (`.pytest_cache/`)
- Linter cache (`.ruff_cache/`)
- Coverage files (`.coverage`, `htmlcov/`)

After cleanup, re-run the setup:
```bash
./setup_local_env.sh
```

## Troubleshooting

### `uv` not found after installation

If `uv` is not found after running `setup_local_env.sh`, add it to your PATH:

```bash
export PATH="$HOME/.cargo/bin:$PATH"
```

Or add this line to your shell configuration file (`~/.bashrc`, `~/.zshrc`, etc.).

### Virtual environment activation issues

If you get errors when activating the environment, make sure you're using `source`:

```bash
# Correct
source ./activate_env.sh

# Incorrect
./activate_env.sh
```

### Permission denied when running scripts

Make the scripts executable:

```bash
chmod +x setup_local_env.sh activate_env.sh cleanup_env.sh
```

### Python version mismatch

The project requires Python 3.12+. Check your Python version:

```bash
python3 --version
```

If you need to install Python 3.12, visit [python.org](https://www.python.org/downloads/) or use your system's package manager.

### Dependencies not installing

If dependencies fail to install, try:

1. Clean the environment:
   ```bash
   ./cleanup_env.sh
   ```

2. Re-run setup:
   ```bash
   ./setup_local_env.sh
   ```

3. If the issue persists, check the `uv.lock` file is in sync:
   ```bash
   uv lock --check
   ```
