"""add missing gemini 2.5 models and common model variants

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-03-13 00:03:00.000000

Adds models that the seed migration missed, including gemini-2.5-flash
which Google released after the initial seed was written.
"""
from typing import Sequence, Union
import uuid

from alembic import op
import sqlalchemy as sa

revision: str = "e5f6a7b8c9d0"
down_revision: Union[str, None] = "d4e5f6a7b8c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

GOOGLE_ID    = "00000000-0000-0000-0000-000000000003"
OPENAI_ID    = "00000000-0000-0000-0000-000000000001"
ANTHROPIC_ID = "00000000-0000-0000-0000-000000000002"


def _insert_model(conn, provider_id, name, display_name, inp, out, cat, vision=False):
    """Insert model only if it doesn't already exist."""
    exists = conn.execute(
        sa.text("SELECT 1 FROM models WHERE name = :name"),
        {"name": name},
    ).fetchone()
    if exists:
        return
    conn.execute(sa.text("""
        INSERT INTO models
          (id, provider_id, name, display_name,
           cost_per_1m_input_tokens, cost_per_1m_output_tokens,
           category, supports_vision, supports_code, is_active)
        VALUES
          (:id, :provider_id, :name, :display_name,
           :inp, :out, :cat, :vision, true, true)
    """).bindparams(
        id=str(uuid.uuid4()),
        provider_id=provider_id,
        name=name,
        display_name=display_name,
        inp=inp,
        out=out,
        cat=cat,
        vision=vision,
    ))


def upgrade() -> None:
    conn = op.get_bind()

    # --- Google Gemini 2.5 ---
    _insert_model(conn, GOOGLE_ID, "gemini-2.5-flash",     "Gemini 2.5 Flash",      0.15,  0.60, "economy",  True)
    _insert_model(conn, GOOGLE_ID, "gemini-2.5-pro",       "Gemini 2.5 Pro",        1.25,  10.00, "flagship", True)
    _insert_model(conn, GOOGLE_ID, "gemini-2.5-flash-preview-04-17", "Gemini 2.5 Flash Preview", 0.15, 0.60, "economy", True)
    _insert_model(conn, GOOGLE_ID, "gemini-2.0-flash-exp", "Gemini 2.0 Flash Exp",  0.00,  0.00, "economy",  True)

    # --- OpenAI versioned variants (commonly used in production) ---
    _insert_model(conn, OPENAI_ID, "gpt-4o-2024-11-20",    "GPT-4o (Nov 2024)",     2.50,  10.00, "flagship", True)
    _insert_model(conn, OPENAI_ID, "gpt-4o-2024-08-06",    "GPT-4o (Aug 2024)",     2.50,  10.00, "flagship", True)
    _insert_model(conn, OPENAI_ID, "gpt-4o-mini-2024-07-18", "GPT-4o Mini (Jul 2024)", 0.15, 0.60, "economy", True)
    _insert_model(conn, OPENAI_ID, "gpt-4.1",              "GPT-4.1",               2.00,  8.00, "flagship", True)
    _insert_model(conn, OPENAI_ID, "gpt-4.1-mini",         "GPT-4.1 Mini",          0.40,  1.60, "economy",  False)

    # --- Anthropic versioned variants ---
    _insert_model(conn, ANTHROPIC_ID, "claude-3-7-sonnet-20250219", "Claude 3.7 Sonnet", 3.00, 15.00, "flagship", True)


def downgrade() -> None:
    models_to_remove = [
        "gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.5-flash-preview-04-17",
        "gemini-2.0-flash-exp", "gpt-4o-2024-11-20", "gpt-4o-2024-08-06",
        "gpt-4o-mini-2024-07-18", "gpt-4.1", "gpt-4.1-mini", "claude-3-7-sonnet-20250219",
    ]
    op.execute(
        sa.text("DELETE FROM models WHERE name = ANY(:names)").bindparams(
            names=models_to_remove
        )
    )
