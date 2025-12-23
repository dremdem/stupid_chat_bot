"""Add user_id column to chat_sessions table

Revision ID: a1b2c3d4e5f6
Revises: 676dc7471bc4
Create Date: 2025-12-23 12:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "676dc7471bc4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add user_id column to chat_sessions table
    op.add_column(
        "chat_sessions",
        sa.Column("user_id", sa.String(length=36), nullable=False),
    )
    # Create index for efficient user-based queries
    op.create_index(
        op.f("ix_chat_sessions_user_id"),
        "chat_sessions",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    # Remove index and column
    op.drop_index(op.f("ix_chat_sessions_user_id"), table_name="chat_sessions")
    op.drop_column("chat_sessions", "user_id")
