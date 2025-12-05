FROM python:3.12-slim

WORKDIR /app

# Install uv for faster package installation
RUN pip install uv

# Copy project files for dependency installation
COPY pyproject.toml uv.lock ./

# Install dependencies from lock file (production only, no editable install)
RUN uv sync --frozen --no-dev --no-editable

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Command will be overridden by docker compose
# Use uv run to execute within the virtual environment
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
