"""Crée la table ag_analyses pour l'analyse comparative des documents AG

Revision ID: 003
Revises: 002
Create Date: 2026-05-27
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ag_analyses",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("triggered_by", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("fec_document_id", UUID(as_uuid=True), sa.ForeignKey("documents.id"), nullable=False),
        sa.Column("budget_document_id", UUID(as_uuid=True), sa.ForeignKey("documents.id"), nullable=True),
        sa.Column("social_document_id", UUID(as_uuid=True), sa.ForeignKey("documents.id"), nullable=True),
        sa.Column("marches_document_id", UUID(as_uuid=True), sa.ForeignKey("documents.id"), nullable=True),
        sa.Column("activites_document_id", UUID(as_uuid=True), sa.ForeignKey("documents.id"), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="PENDING"),
        sa.Column("budget_comparison", JSON, nullable=True),
        sa.Column("masse_salariale_check", JSON, nullable=True),
        sa.Column("marches_check", JSON, nullable=True),
        sa.Column("activites_check", JSON, nullable=True),
        sa.Column("coherence_score", sa.Float, nullable=True),
        sa.Column("risk_level", sa.String(10), nullable=True),
        sa.Column("ai_synthesis", sa.Text, nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
    )
    op.create_index("ix_ag_analyses_tenant_id", "ag_analyses", ["tenant_id"])
    op.create_index("ix_ag_analyses_created_at", "ag_analyses", ["created_at"])


def downgrade() -> None:
    op.drop_table("ag_analyses")
