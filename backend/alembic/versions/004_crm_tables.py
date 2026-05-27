"""Crée les tables CRM : crm_clients, crm_contacts, activity_logs

Revision ID: 004
Revises: 003
Create Date: 2026-05-27
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON, ARRAY

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── crm_clients ──────────────────────────────────────────────────────────
    op.create_table(
        "crm_clients",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        # Lien optionnel vers le tenant (NULL si encore prospect)
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="SET NULL"), nullable=True),
        sa.Column("assigned_to", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        # Identité
        sa.Column("company_name", sa.String(200), nullable=False),
        sa.Column("rccm", sa.String(50), nullable=True),
        sa.Column("nif", sa.String(50), nullable=True),
        sa.Column("sector", sa.String(100), nullable=True),
        sa.Column("country", sa.String(50), nullable=False, server_default="BF"),
        sa.Column("city", sa.String(100), nullable=True),
        sa.Column("address", sa.Text, nullable=True),
        sa.Column("website", sa.String(200), nullable=True),
        # Pipeline
        sa.Column("lifecycle_status", sa.String(20), nullable=False, server_default="PROSPECT"),
        sa.Column("pipeline_stage", sa.String(20), nullable=False, server_default="PROSPECT"),
        sa.Column("deal_value", sa.Numeric(14, 2), nullable=True),
        sa.Column("expected_close_date", sa.Date, nullable=True),
        sa.Column("source", sa.String(50), nullable=True),
        sa.Column("lost_reason", sa.Text, nullable=True),
        # Santé & suivi
        sa.Column("health_score", sa.Integer, nullable=True),
        sa.Column("tags", JSON, nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("trial_ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_contact_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_crm_clients_tenant_id", "crm_clients", ["tenant_id"])
    op.create_index("ix_crm_clients_lifecycle_status", "crm_clients", ["lifecycle_status"])
    op.create_index("ix_crm_clients_pipeline_stage", "crm_clients", ["pipeline_stage"])

    # ── crm_contacts ─────────────────────────────────────────────────────────
    op.create_table(
        "crm_contacts",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("crm_client_id", UUID(as_uuid=True), sa.ForeignKey("crm_clients.id", ondelete="CASCADE"), nullable=False),
        sa.Column("full_name", sa.String(200), nullable=False),
        sa.Column("role", sa.String(100), nullable=True),
        sa.Column("email", sa.String(200), nullable=True),
        sa.Column("phone", sa.String(30), nullable=True),
        sa.Column("is_primary", sa.Boolean, nullable=False, server_default="false"),
    )
    op.create_index("ix_crm_contacts_client_id", "crm_contacts", ["crm_client_id"])

    # ── activity_logs ─────────────────────────────────────────────────────────
    op.create_table(
        "activity_logs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("crm_client_id", UUID(as_uuid=True), sa.ForeignKey("crm_clients.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_by", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("activity_type", sa.String(30), nullable=False),  # CALL, EMAIL, MEETING, DEMO, NOTE, RELANCE
        sa.Column("subject", sa.String(300), nullable=True),
        sa.Column("body", sa.Text, nullable=True),
        sa.Column("outcome", sa.String(100), nullable=True),
        sa.Column("next_action", sa.Text, nullable=True),
        sa.Column("next_action_date", sa.Date, nullable=True),
        sa.Column("duration_minutes", sa.Integer, nullable=True),
    )
    op.create_index("ix_activity_logs_client_id", "activity_logs", ["crm_client_id"])
    op.create_index("ix_activity_logs_created_at", "activity_logs", ["created_at"])


def downgrade() -> None:
    op.drop_table("activity_logs")
    op.drop_table("crm_contacts")
    op.drop_table("crm_clients")
