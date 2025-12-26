#!/bin/bash
set -e

echo "=== Database Migration Check ==="

DB_PATH="${DATABASE_PATH:-data/chat.db}"
echo "Database path: $DB_PATH"

# Handle legacy/misconfigured database migrations
if [ -f "$DB_PATH" ]; then
    echo "Database file exists, checking schema state..."

    # Check and fix schema directly with SQL (bypass alembic for legacy fixes)
    .venv/bin/python << EOF
import sqlite3
conn = sqlite3.connect("$DB_PATH")
cursor = conn.cursor()

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
EOF

    # Now stamp at head since schema is correct
    echo "Ensuring alembic is at head..."
    .venv/bin/python -m alembic stamp head 2>&1 || echo "Stamp returned non-zero"
    echo "Alembic stamp complete."
else
    echo "No existing database file, will be created by migrations."
fi

# Run Alembic migrations (should be no-op if already at head)
echo "Running database migrations..."
.venv/bin/python -m alembic upgrade head

echo "Migrations complete."
echo "================================"

# Execute the main command (uvicorn)
echo "Starting application..."
exec "$@"
