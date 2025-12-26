#!/bin/bash
set -e

echo "=== Database Migration Check ==="

DB_PATH="${DATABASE_PATH:-data/chat.db}"
echo "Database path: $DB_PATH"

# Simple check: if database exists but has no alembic_version, stamp it
# This is a one-time fix for legacy databases created before alembic was introduced
if [ -f "$DB_PATH" ]; then
    echo "Database file exists, checking for alembic_version table..."

    # Check if alembic_version table exists using sqlite3
    # Use timeout and error handling - if check fails, assume legacy (stamp is idempotent)
    HAS_ALEMBIC=$(.venv/bin/python -c "
import sqlite3
import sys
try:
    conn = sqlite3.connect('$DB_PATH', timeout=5)
    cursor = conn.cursor()
    cursor.execute('SELECT name FROM sqlite_master WHERE type=\"table\" AND name=\"alembic_version\"')
    result = cursor.fetchone()
    conn.close()
    print('yes' if result else 'no')
except Exception as e:
    print(f'ERROR: {e}', file=sys.stderr)
    print('unknown')
" 2>&1) || HAS_ALEMBIC="error"

    echo "Has alembic_version table: $HAS_ALEMBIC"

    # Stamp if no alembic_version OR if check failed (stamp is safe to run multiple times)
    if [ "$HAS_ALEMBIC" != "yes" ]; then
        if [ "$HAS_ALEMBIC" = "no" ]; then
            echo "Legacy database detected (no alembic_version table)"
        else
            echo "Could not determine database state ($HAS_ALEMBIC), will stamp to be safe"
        fi
        echo "Stamping database with current migration head..."
        .venv/bin/python -m alembic stamp head || echo "Stamp command returned non-zero (may already be stamped)"
        echo "Database stamp complete."
    else
        echo "Database already has migration tracking."
    fi
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
