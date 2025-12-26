#!/bin/bash
set -e

echo "=== Database Migration Check ==="

# Debug: Show database path
echo "DATABASE_PATH=${DATABASE_PATH:-'not set, using default'}"

# Check if this is a legacy database (has tables but no alembic_version)
# This handles databases created before alembic migrations were introduced
check_legacy_db() {
    .venv/bin/python -c "
import sqlite3
import os
import sys

try:
    db_path = os.environ.get('DATABASE_PATH', 'data/chat.db')
    print(f'Checking database at: {db_path}', file=sys.stderr)

    if not os.path.exists(db_path):
        print(f'Database file does not exist', file=sys.stderr)
        print('fresh')
        sys.exit(0)

    print(f'Database file exists, checking tables...', file=sys.stderr)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check if alembic_version exists
    cursor.execute(\"SELECT name FROM sqlite_master WHERE type='table' AND name='alembic_version'\")
    has_alembic = cursor.fetchone() is not None
    print(f'Has alembic_version table: {has_alembic}', file=sys.stderr)

    # Check if chat_sessions exists (indicator of existing data)
    cursor.execute(\"SELECT name FROM sqlite_master WHERE type='table' AND name='chat_sessions'\")
    has_tables = cursor.fetchone() is not None
    print(f'Has chat_sessions table: {has_tables}', file=sys.stderr)

    conn.close()

    if has_tables and not has_alembic:
        print('legacy')
    elif has_alembic:
        print('migrated')
    else:
        print('fresh')
except Exception as e:
    print(f'Error checking database: {e}', file=sys.stderr)
    print('error')
" 2>&1
}

DB_STATE=$(check_legacy_db | tail -1)
echo "Database state: $DB_STATE"

if [ "$DB_STATE" = "legacy" ]; then
    echo "Legacy database detected - stamping with current migration head..."
    .venv/bin/python -m alembic stamp head
    echo "Database stamped. Future migrations will run normally."
elif [ "$DB_STATE" = "error" ]; then
    echo "WARNING: Could not determine database state, proceeding with normal migration..."
fi

# Run Alembic migrations
echo "Running database migrations..."
.venv/bin/python -m alembic upgrade head

echo "Migrations complete."
echo "================================"

# Execute the main command (uvicorn)
echo "Starting application..."
exec "$@"
