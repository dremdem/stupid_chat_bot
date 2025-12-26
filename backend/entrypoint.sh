#!/bin/bash
set -e

echo "=== Database Migration Check ==="

DB_PATH="${DATABASE_PATH:-data/chat.db}"
echo "Database path: $DB_PATH"

# Handle legacy/misconfigured database migrations
if [ -f "$DB_PATH" ]; then
    echo "Database file exists, checking schema state..."

    # Check if messages.user_id column exists (this is the key indicator)
    DB_STATE=$(.venv/bin/python << EOF
import sqlite3
conn = sqlite3.connect("$DB_PATH")
cursor = conn.cursor()

# Check if messages.user_id column exists
cursor.execute("PRAGMA table_info(messages)")
columns = [row[1] for row in cursor.fetchall()]
has_user_id = "user_id" in columns

print("has_user_id" if has_user_id else "missing_user_id")
conn.close()
EOF
)

    echo "Schema state: $DB_STATE"

    if [ "$DB_STATE" = "missing_user_id" ]; then
        echo "messages.user_id column missing!"
        echo "Resetting alembic to a1b2c3d4e5f6 so upgrade can add the column..."
        # Force stamp to the revision BEFORE user_id was added
        .venv/bin/python -m alembic stamp --purge a1b2c3d4e5f6 2>&1 || echo "Stamp failed"
        echo "Stamp complete - upgrade will add missing columns."
    else
        echo "Schema looks correct (has user_id column)."
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
