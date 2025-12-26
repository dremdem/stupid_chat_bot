#!/bin/bash
set -e

echo "=== Database Migration Check ==="

# Check if this is a legacy database (has tables but no alembic_version)
# This handles databases created before alembic migrations were introduced
check_legacy_db() {
    .venv/bin/python -c "
import sqlite3
import os

db_path = os.environ.get('DATABASE_PATH', 'data/chat.db')
if not os.path.exists(db_path):
    print('fresh')  # No database yet
    exit(0)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check if alembic_version exists
cursor.execute(\"SELECT name FROM sqlite_master WHERE type='table' AND name='alembic_version'\")
has_alembic = cursor.fetchone() is not None

# Check if chat_sessions exists (indicator of existing data)
cursor.execute(\"SELECT name FROM sqlite_master WHERE type='table' AND name='chat_sessions'\")
has_tables = cursor.fetchone() is not None

conn.close()

if has_tables and not has_alembic:
    print('legacy')  # Existing database without migration tracking
elif has_alembic:
    print('migrated')  # Already has migration tracking
else:
    print('fresh')  # Empty or new database
"
}

DB_STATE=$(check_legacy_db)
echo "Database state: $DB_STATE"

if [ "$DB_STATE" = "legacy" ]; then
    echo "Legacy database detected - stamping with current migration head..."
    .venv/bin/python -m alembic stamp head
    echo "Database stamped. Future migrations will run normally."
fi

# Run Alembic migrations
echo "Running database migrations..."
.venv/bin/python -m alembic upgrade head

echo "Migrations complete."
echo "================================"

# Execute the main command (uvicorn)
echo "Starting application..."
exec "$@"
