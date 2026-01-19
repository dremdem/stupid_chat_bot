#!/bin/bash
set -e

echo "=== Database Migration Check ==="

DB_PATH="${DATABASE_PATH:-data/chat.db}"
echo "Database path: $DB_PATH"

# Handle legacy/misconfigured database migrations
if [ -f "$DB_PATH" ]; then
    echo "Database file exists, checking schema state..."

    # Check if alembic_version table exists and fix legacy issues
    .venv/bin/python << EOF
import sqlite3
conn = sqlite3.connect("$DB_PATH")
cursor = conn.cursor()

# Check if alembic_version table exists
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='alembic_version'")
has_alembic = cursor.fetchone() is not None

# Check if messages.user_id column exists
cursor.execute("PRAGMA table_info(messages)")
columns = [row[1] for row in cursor.fetchall()]
has_user_id = "user_id" in columns

if has_user_id:
    print("Schema OK: messages.user_id exists")
else:
    print("FIXING: Adding messages.user_id column directly...")
    cursor.execute("ALTER TABLE messages ADD COLUMN user_id VARCHAR(36)")
    print("Column added successfully")

conn.commit()
conn.close()

# Return whether alembic table exists (0 = exists, 1 = not exists)
exit(0 if has_alembic else 1)
EOF
    HAS_ALEMBIC=$?

    # Only stamp if alembic wasn't tracking this database
    if [ $HAS_ALEMBIC -ne 0 ]; then
        echo "No alembic version table found, stamping at base migration..."
        # Stamp at the first migration that includes users table
        .venv/bin/python -m alembic stamp b2c3d4e5f6a7 2>&1 || echo "Stamp returned non-zero"
        echo "Alembic stamp complete."
    else
        echo "Alembic version table exists, will run normal migrations."
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
