"""activate google provider and upsert provider records

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-03-13 00:02:00.000000

This migration is idempotent: it inserts providers if missing, then
sets google (and openai/anthropic) to is_active=true.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, None] = "c3d4e5f6a7b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

OPENAI_ID    = "00000000-0000-0000-0000-000000000001"
ANTHROPIC_ID = "00000000-0000-0000-0000-000000000002"
GOOGLE_ID    = "00000000-0000-0000-0000-000000000003"
MISTRAL_ID   = "00000000-0000-0000-0000-000000000004"


def upgrade() -> None:
    conn = op.get_bind()

    # Upsert all 4 providers (INSERT if not exists, UPDATE if exists)
    conn.execute(sa.text("""
        INSERT INTO providers (id, name, display_name, base_url, is_active)
        VALUES
          (:openai_id,    'openai',    'OpenAI',        'https://api.openai.com/v1',                              true),
          (:anthropic_id, 'anthropic', 'Anthropic',     'https://api.anthropic.com/v1',                           true),
          (:google_id,    'google',    'Google Gemini', 'https://generativelanguage.googleapis.com/v1beta',       true),
          (:mistral_id,   'mistral',   'Mistral AI',    'https://api.mistral.ai/v1',                              false)
        ON CONFLICT (name) DO UPDATE
          SET is_active  = EXCLUDED.is_active,
              base_url   = EXCLUDED.base_url,
              display_name = EXCLUDED.display_name
    """).bindparams(
        openai_id=OPENAI_ID,
        anthropic_id=ANTHROPIC_ID,
        google_id=GOOGLE_ID,
        mistral_id=MISTRAL_ID,
    ))


def downgrade() -> None:
    op.execute(sa.text(
        "UPDATE providers SET is_active=false WHERE name='google'"
    ))
