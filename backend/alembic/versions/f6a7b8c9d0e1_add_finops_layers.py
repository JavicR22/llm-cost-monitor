"""add finops cost attribution layers

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-03-14 00:00:00.000000

Adds:
- projects table  (Org → Project → budget_limit)
- teams table     (Project → Team  → budget_limit)
- service_api_keys: project_id, team_id, owner_user_id (all nullable)
- usage_logs:      project_id, team_id, user_id         (all nullable)

All FKs are nullable so existing rows/keys are unaffected.
Idempotent: safe to re-run if a previous attempt partially applied.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql

revision: str = "f6a7b8c9d0e1"
down_revision: Union[str, Sequence[str], None] = "e5f6a7b8c9d0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(inspector, name: str) -> bool:
    return name in inspector.get_table_names()


def _column_exists(inspector, table: str, column: str) -> bool:
    return any(c["name"] == column for c in inspector.get_columns(table))


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    # ------------------------------------------------------------------
    # projects
    # NOTE: No index=True on columns — we create indexes explicitly below
    #       to avoid duplicate-name errors.
    # ------------------------------------------------------------------
    if not _table_exists(inspector, "projects"):
        op.create_table(
            "projects",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column(
                "organization_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("organizations.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("name", sa.String(255), nullable=False),
            sa.Column("description", sa.String(1000), nullable=True),
            sa.Column("budget_limit", sa.Numeric(12, 4), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
        )

    op.create_index(
        "ix_projects_organization_id", "projects", ["organization_id"], if_not_exists=True
    )

    # ------------------------------------------------------------------
    # teams
    # ------------------------------------------------------------------
    if not _table_exists(inspector, "teams"):
        op.create_table(
            "teams",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column(
                "project_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("projects.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("name", sa.String(255), nullable=False),
            sa.Column("budget_limit", sa.Numeric(12, 4), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
        )

    op.create_index(
        "ix_teams_project_id", "teams", ["project_id"], if_not_exists=True
    )

    # ------------------------------------------------------------------
    # service_api_keys — add finops attribution columns
    # ------------------------------------------------------------------
    if not _column_exists(inspector, "service_api_keys", "project_id"):
        op.add_column(
            "service_api_keys",
            sa.Column(
                "project_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("projects.id", ondelete="SET NULL"),
                nullable=True,
            ),
        )

    if not _column_exists(inspector, "service_api_keys", "team_id"):
        op.add_column(
            "service_api_keys",
            sa.Column(
                "team_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("teams.id", ondelete="SET NULL"),
                nullable=True,
            ),
        )

    if not _column_exists(inspector, "service_api_keys", "owner_user_id"):
        op.add_column(
            "service_api_keys",
            sa.Column(
                "owner_user_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("users.id", ondelete="SET NULL"),
                nullable=True,
            ),
        )

    op.create_index(
        "ix_service_api_keys_project_id", "service_api_keys", ["project_id"], if_not_exists=True
    )
    op.create_index(
        "ix_service_api_keys_team_id", "service_api_keys", ["team_id"], if_not_exists=True
    )
    op.create_index(
        "ix_service_api_keys_owner_user_id", "service_api_keys", ["owner_user_id"], if_not_exists=True
    )

    # ------------------------------------------------------------------
    # usage_logs — add finops attribution columns
    # ------------------------------------------------------------------
    if not _column_exists(inspector, "usage_logs", "project_id"):
        op.add_column(
            "usage_logs",
            sa.Column(
                "project_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("projects.id", ondelete="SET NULL"),
                nullable=True,
            ),
        )

    if not _column_exists(inspector, "usage_logs", "team_id"):
        op.add_column(
            "usage_logs",
            sa.Column(
                "team_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("teams.id", ondelete="SET NULL"),
                nullable=True,
            ),
        )

    if not _column_exists(inspector, "usage_logs", "user_id"):
        op.add_column(
            "usage_logs",
            sa.Column(
                "user_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("users.id", ondelete="SET NULL"),
                nullable=True,
            ),
        )

    op.create_index(
        "ix_usage_logs_project_id", "usage_logs", ["project_id"], if_not_exists=True
    )
    op.create_index(
        "ix_usage_logs_team_id", "usage_logs", ["team_id"], if_not_exists=True
    )
    op.create_index(
        "ix_usage_logs_user_id", "usage_logs", ["user_id"], if_not_exists=True
    )


def downgrade() -> None:
    # usage_logs
    op.drop_index("ix_usage_logs_user_id", table_name="usage_logs", if_exists=True)
    op.drop_index("ix_usage_logs_team_id", table_name="usage_logs", if_exists=True)
    op.drop_index("ix_usage_logs_project_id", table_name="usage_logs", if_exists=True)

    bind = op.get_bind()
    inspector = inspect(bind)

    if _column_exists(inspector, "usage_logs", "user_id"):
        op.drop_column("usage_logs", "user_id")
    if _column_exists(inspector, "usage_logs", "team_id"):
        op.drop_column("usage_logs", "team_id")
    if _column_exists(inspector, "usage_logs", "project_id"):
        op.drop_column("usage_logs", "project_id")

    # service_api_keys
    op.drop_index("ix_service_api_keys_owner_user_id", table_name="service_api_keys", if_exists=True)
    op.drop_index("ix_service_api_keys_team_id", table_name="service_api_keys", if_exists=True)
    op.drop_index("ix_service_api_keys_project_id", table_name="service_api_keys", if_exists=True)

    if _column_exists(inspector, "service_api_keys", "owner_user_id"):
        op.drop_column("service_api_keys", "owner_user_id")
    if _column_exists(inspector, "service_api_keys", "team_id"):
        op.drop_column("service_api_keys", "team_id")
    if _column_exists(inspector, "service_api_keys", "project_id"):
        op.drop_column("service_api_keys", "project_id")

    # teams / projects
    op.drop_index("ix_teams_project_id", table_name="teams", if_exists=True)
    op.drop_table("teams", if_exists=True)
    op.drop_index("ix_projects_organization_id", table_name="projects", if_exists=True)
    op.drop_table("projects", if_exists=True)
