"""Add report_schedule table and user receive_reports field

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2025-01-19 12:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, None] = "c3d4e5f6a7b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create report_schedule table (singleton - only one row)
    op.create_table(
        "report_schedule",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "schedule_type",
            sa.String(length=20),
            nullable=False,
            server_default="weekly",
        ),
        sa.Column(
            "day_of_week",
            sa.String(length=10),
            nullable=False,
            server_default="mon",
        ),
        sa.Column("hour", sa.Integer(), nullable=False, server_default="9"),
        sa.Column("minute", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("updated_by", sa.Uuid(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Add receive_reports column to users table
    op.add_column(
        "users",
        sa.Column(
            "receive_reports",
            sa.Boolean(),
            nullable=False,
            server_default="false",
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "receive_reports")
    op.drop_table("report_schedule")
