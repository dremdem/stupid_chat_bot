# Base stage: Production dependencies only
FROM python:3.12-slim AS base

WORKDIR /app

# Install uv for faster package installation
RUN pip install uv

# Copy project files for dependency installation
COPY pyproject.toml uv.lock ./

# Install production dependencies from lock file
RUN uv sync --frozen --no-dev --no-editable

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Command will be overridden by docker compose
# Use uv run to execute within the virtual environment
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]


# Dev stage: Base + all dev dependencies (linters + test tools)
FROM base AS dev

# Install all dev dependencies (linters + test tools)
RUN uv sync --frozen --all-extras --no-editable

# This stage is used for development with hot-reload and running tests
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]


# Prod stage: Optimized production image (alias for base)
FROM base AS prod

# This stage is explicitly for production deployment
# Uses the base stage without any dev dependencies
