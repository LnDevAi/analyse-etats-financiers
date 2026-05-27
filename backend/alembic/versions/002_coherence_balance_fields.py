"""Ajoute les colonnes coherence_check_result et balance_reconciliation_result à analyses

Revision ID: 002
Revises: 001
Create Date: 2026-05-27
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("analyses", sa.Column("coherence_check_result", JSON, nullable=True))
    op.add_column("analyses", sa.Column("balance_reconciliation_result", JSON, nullable=True))


def downgrade() -> None:
    op.drop_column("analyses", "coherence_check_result")
    op.drop_column("analyses", "balance_reconciliation_result")
