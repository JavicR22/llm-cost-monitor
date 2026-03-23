"""seed providers and models

Revision ID: b2c3d4e5f6a7
Revises: 41245f4f9313
Create Date: 2026-03-13 00:00:00.000000

"""
from typing import Sequence, Union
import uuid

from alembic import op
import sqlalchemy as sa

revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, None] = "41245f4f9313"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Fixed UUIDs so re-running is idempotent
OPENAI_ID    = "00000000-0000-0000-0000-000000000001"
ANTHROPIC_ID = "00000000-0000-0000-0000-000000000002"
GOOGLE_ID    = "00000000-0000-0000-0000-000000000003"
MISTRAL_ID   = "00000000-0000-0000-0000-000000000004"


def upgrade() -> None:
    providers = op.get_bind().execute(
        sa.text("SELECT id FROM providers WHERE name = 'openai'")
    ).fetchone()
    if providers:
        return  # Already seeded

    # --- Providers ---
    op.execute(sa.text("""
        INSERT INTO providers (id, name, display_name, base_url, is_active) VALUES
        (:openai_id,    'openai',    'OpenAI',        'https://api.openai.com/v1',               true),
        (:anthropic_id, 'anthropic', 'Anthropic',     'https://api.anthropic.com/v1',            true),
        (:google_id,    'google',    'Google Gemini', 'https://generativelanguage.googleapis.com/v1beta', true),
        (:mistral_id,   'mistral',   'Mistral AI',    'https://api.mistral.ai/v1',               false)
    """).bindparams(
        openai_id=OPENAI_ID,
        anthropic_id=ANTHROPIC_ID,
        google_id=GOOGLE_ID,
        mistral_id=MISTRAL_ID,
    ))

    # --- OpenAI Models ---
    openai_models = [
        ("gpt-4o",              "GPT-4o",            2.50,  10.00, "flagship", True,  True),
        ("gpt-4o-mini",         "GPT-4o Mini",        0.15,   0.60, "economy",  True,  True),
        ("gpt-4-turbo",         "GPT-4 Turbo",       10.00,  30.00, "flagship", True,  True),
        ("gpt-3.5-turbo",       "GPT-3.5 Turbo",      0.50,   1.50, "economy",  False, True),
        ("o1",                  "o1",                15.00,  60.00, "flagship", False, True),
        ("o1-mini",             "o1 Mini",            3.00,  12.00, "mid",      False, True),
        ("o3-mini",             "o3 Mini",            1.10,   4.40, "mid",      False, True),
    ]
    for name, display, inp, out, cat, vision, active in openai_models:
        op.execute(sa.text("""
            INSERT INTO models
              (id, provider_id, name, display_name,
               cost_per_1m_input_tokens, cost_per_1m_output_tokens,
               category, supports_vision, supports_code, is_active)
            VALUES
              (:id, :provider_id, :name, :display_name, :inp, :out,
               :cat, :vision, true, :active)
        """).bindparams(
            id=str(uuid.uuid4()),
            provider_id=OPENAI_ID,
            name=name,
            display_name=display,
            inp=inp,
            out=out,
            cat=cat,
            vision=vision,
            active=active,
        ))

    # --- Anthropic Models ---
    anthropic_models = [
        ("claude-opus-4-6",              "Claude Opus 4.6",         15.00, 75.00, "flagship", True,  True),
        ("claude-sonnet-4-6",            "Claude Sonnet 4.6",        3.00, 15.00, "flagship", True,  True),
        ("claude-3-5-sonnet-20241022",   "Claude 3.5 Sonnet",        3.00, 15.00, "mid",      True,  True),
        ("claude-haiku-4-5-20251001",    "Claude Haiku 4.5",         0.80,  4.00, "economy",  False, True),
        ("claude-3-5-haiku-20241022",    "Claude 3.5 Haiku",         0.80,  4.00, "economy",  False, True),
        ("claude-3-opus-20240229",       "Claude 3 Opus",           15.00, 75.00, "flagship", True,  True),
    ]
    for name, display, inp, out, cat, vision, active in anthropic_models:
        op.execute(sa.text("""
            INSERT INTO models
              (id, provider_id, name, display_name,
               cost_per_1m_input_tokens, cost_per_1m_output_tokens,
               category, supports_vision, supports_code, is_active)
            VALUES
              (:id, :provider_id, :name, :display_name, :inp, :out,
               :cat, :vision, true, :active)
        """).bindparams(
            id=str(uuid.uuid4()),
            provider_id=ANTHROPIC_ID,
            name=name,
            display_name=display,
            inp=inp,
            out=out,
            cat=cat,
            vision=vision,
            active=active,
        ))

    # --- Mistral Models ---
    mistral_models = [
        ("mistral-large-latest",  "Mistral Large",   2.00,  6.00, "flagship", False, True),
        ("mistral-small-latest",  "Mistral Small",   0.20,  0.60, "economy",  False, True),
        ("codestral-latest",      "Codestral",       0.20,  0.60, "mid",      False, True),
    ]
    for name, display, inp, out, cat, vision, active in mistral_models:
        op.execute(sa.text("""
            INSERT INTO models
              (id, provider_id, name, display_name,
               cost_per_1m_input_tokens, cost_per_1m_output_tokens,
               category, supports_vision, supports_code, is_active)
            VALUES
              (:id, :provider_id, :name, :display_name, :inp, :out,
               :cat, :vision, true, :active)
        """).bindparams(
            id=str(uuid.uuid4()),
            provider_id=MISTRAL_ID,
            name=name,
            display_name=display,
            inp=inp,
            out=out,
            cat=cat,
            vision=vision,
            active=active,
        ))

    # --- Google Gemini Models ---
    google_models = [
        ("gemini-2.0-flash",      "Gemini 2.0 Flash",     0.10,  0.40, "economy",  True,  True),
        ("gemini-1.5-pro",        "Gemini 1.5 Pro",       1.25,  5.00, "flagship", True,  True),
        ("gemini-1.5-flash",      "Gemini 1.5 Flash",     0.075, 0.30, "economy",  True,  True),
    ]
    for name, display, inp, out, cat, vision, active in google_models:
        op.execute(sa.text("""
            INSERT INTO models
              (id, provider_id, name, display_name,
               cost_per_1m_input_tokens, cost_per_1m_output_tokens,
               category, supports_vision, supports_code, is_active)
            VALUES
              (:id, :provider_id, :name, :display_name, :inp, :out,
               :cat, :vision, true, :active)
        """).bindparams(
            id=str(uuid.uuid4()),
            provider_id=GOOGLE_ID,
            name=name,
            display_name=display,
            inp=inp,
            out=out,
            cat=cat,
            vision=vision,
            active=active,
        ))


def downgrade() -> None:
    op.execute(sa.text("DELETE FROM models WHERE provider_id IN (:o, :a, :g, :m)").bindparams(
        o=OPENAI_ID, a=ANTHROPIC_ID, g=GOOGLE_ID, m=MISTRAL_ID
    ))
    op.execute(sa.text("DELETE FROM providers WHERE id IN (:o, :a, :g, :m)").bindparams(
        o=OPENAI_ID, a=ANTHROPIC_ID, g=GOOGLE_ID, m=MISTRAL_ID
    ))
