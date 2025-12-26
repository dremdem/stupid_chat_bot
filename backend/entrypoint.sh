#!/bin/bash
set -e

echo "=== Database Migration Check ==="

DB_PATH="${DATABASE_PATH:-data/chat.db}"
echo "Database path: $DB_PATH"

# If database file exists, always stamp it first
# This handles legacy databases created before alembic was introduced
# Stamping is idempotent - safe to run multiple times
if [ -f "$DB_PATH" ]; then
    echo "Database file exists, stamping with current migration head..."
    # Stamp is idempotent - if already stamped, this is a no-op
    .venv/bin/python -m alembic stamp head 2>&1 || echo "Note: stamp returned non-zero (likely already at head)"
    echo "Stamp complete."
else
    echo "No existing database file, will be created by migrations."
fi

# Run Alembic migrations
echo "Running database migrations..."
.venv/bin/python -m alembic upgrade head

echo "Migrations complete."
echo "================================"

# Execute the main command (uvicorn)
echo "Starting application..."
exec "$@"
