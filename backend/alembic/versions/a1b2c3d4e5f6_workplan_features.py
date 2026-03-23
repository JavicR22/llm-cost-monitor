"""workplan features: new roles, user fields, developer_api_keys table

Revision ID: a1b2c3d4e5f6
Revises: f6a7b8c9d0e1
Create Date: 2026-03-17 00:00:00.000000

Changes:
- Add 'project_leader' and 'developer' values to user_role enum
- Add assigned_project_id, assigned_team_id, has_seen_key_modal to users table
- Create developer_api_keys table (one personal key per developer)

Idempotent: safe to re-run if a previous attempt partially applied.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect, text
from sqlalchemy.dialects import postgresql

revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "f6a7b8c9d0e1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(inspector, name: str) -> bool:
    return name in inspector.get_table_names()


def _column_exists(inspector, table: str, column: str) -> bool:
    if not _table_exists(inspector, table):
        return False
    return any(c["name"] == column for c in inspector.get_columns(table))


def _enum_value_exists(bind, enum_name: str, value: str) -> bool:
    """Check if a value already exists in a PostgreSQL enum type."""
    result = bind.execute(
        text(
            "SELECT 1 FROM pg_enum e "
            "JOIN pg_type t ON t.oid = e.enumtypid "
            "WHERE t.typname = :enum_name AND e.enumlabel = :value"
        ),
        {"enum_name": enum_name, "value": value},
    )
    return result.fetchone() is not None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    # ------------------------------------------------------------------
    # 1. Extend user_role enum with new values
    # ------------------------------------------------------------------
    for new_value in ("project_leader", "developer"):
        if not _enum_value_exists(bind, "user_role", new_value):
            # PostgreSQL requires COMMIT before ALTER TYPE ADD VALUE
            # Alembic runs in autocommit=False by default — use execute directly
            bind.execute(
                text(f"ALTER TYPE user_role ADD VALUE IF NOT EXISTS '{new_value}'")
            )

    # ------------------------------------------------------------------
    # 2. Add new columns to users
    # ------------------------------------------------------------------
    if not _column_exists(inspector, "users", "assigned_project_id"):
        op.add_column(
            "users",
            sa.Column(
                "assigned_project_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("projects.id", ondelete="SET NULL"),
                nullable=True,
            ),
        )

    if not _column_exists(inspector, "users", "assigned_team_id"):
        op.add_column(
            "users",
            sa.Column(
                "assigned_team_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("teams.id", ondelete="SET NULL"),
                nullable=True,
            ),
        )

    if not _column_exists(inspector, "users", "has_seen_key_modal"):
        op.add_column(
            "users",
            sa.Column(
                "has_seen_key_modal",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("false"),
            ),
        )

    # ------------------------------------------------------------------
    # 3. Create developer_api_keys table
    # ------------------------------------------------------------------
    if not _table_exists(inspector, "developer_api_keys"):
        op.create_table(
            "developer_api_keys",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column(
                "user_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("users.id", ondelete="CASCADE"),
                nullable=False,
                unique=True,
            ),
            sa.Column("key_prefix", sa.String(50), nullable=False),
            sa.Column("key_hash", sa.String(64), unique=True, nullable=False),
            sa.Column("label", sa.String(100), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
        )

    op.create_index(
        "ix_developer_api_keys_user_id",
        "developer_api_keys",
        ["user_id"],
        if_not_exists=True,
    )
    op.create_index(
        "ix_developer_api_keys_key_hash",
        "developer_api_keys",
        ["key_hash"],
        if_not_exists=True,
    )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    # 3. Drop developer_api_keys
    op.drop_index("ix_developer_api_keys_key_hash", table_name="developer_api_keys", if_exists=True)
    op.drop_index("ix_developer_api_keys_user_id", table_name="developer_api_keys", if_exists=True)
    if _table_exists(inspector, "developer_api_keys"):
        op.drop_table("developer_api_keys")

    # 2. Remove columns from users
    if _column_exists(inspector, "users", "has_seen_key_modal"):
        op.drop_column("users", "has_seen_key_modal")
    if _column_exists(inspector, "users", "assigned_team_id"):
        op.drop_column("users", "assigned_team_id")
    if _column_exists(inspector, "users", "assigned_project_id"):
        op.drop_column("users", "assigned_project_id")

    # Note: PostgreSQL does not support removing enum values (ALTER TYPE DROP VALUE
    # is not available). The project_leader and developer values are left in place
    # on downgrade to avoid data corruption.
