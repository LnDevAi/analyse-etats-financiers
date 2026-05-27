"""Crée les tables billing : subscription_plans, subscriptions, invoices, payments

Revision ID: 005
Revises: 004
Create Date: 2026-05-27
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON

revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── subscription_plans ───────────────────────────────────────────────────
    op.create_table(
        "subscription_plans",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("name", sa.String(50), nullable=False, unique=True),       # STARTER, PRO, ENTERPRISE
        sa.Column("display_name", sa.String(100), nullable=False),
        sa.Column("price_monthly", sa.Numeric(12, 2), nullable=False),       # FCFA/mois
        sa.Column("price_yearly", sa.Numeric(12, 2), nullable=True),         # FCFA/an (remise 15%)
        sa.Column("max_analyses", sa.Integer, nullable=True),                # NULL = illimité
        sa.Column("max_users", sa.Integer, nullable=True),
        sa.Column("max_documents", sa.Integer, nullable=True),
        sa.Column("trial_days", sa.Integer, nullable=False, server_default="14"),
        sa.Column("features", JSON, nullable=True),                          # liste de features incluses
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("sort_order", sa.Integer, nullable=False, server_default="0"),
    )

    # ── subscriptions ────────────────────────────────────────────────────────
    op.create_table(
        "subscriptions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("plan_id", UUID(as_uuid=True), sa.ForeignKey("subscription_plans.id"), nullable=False),
        sa.Column("billing_cycle", sa.String(10), nullable=False, server_default="MONTHLY"),  # MONTHLY / YEARLY
        sa.Column("status", sa.String(20), nullable=False, server_default="TRIAL"),
        # TRIAL, ACTIVE, PAST_DUE, SUSPENDED, CANCELLED
        sa.Column("trial_ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("current_period_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("current_period_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancel_at_period_end", sa.Boolean, nullable=False, server_default="false"),
        # Usage courant (réinitialisé à chaque période)
        sa.Column("analyses_used", sa.Integer, nullable=False, server_default="0"),
        sa.Column("documents_used", sa.Integer, nullable=False, server_default="0"),
    )
    op.create_index("ix_subscriptions_tenant_id", "subscriptions", ["tenant_id"])
    op.create_index("ix_subscriptions_status", "subscriptions", ["status"])

    # ── invoices ─────────────────────────────────────────────────────────────
    op.create_table(
        "invoices",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("subscription_id", UUID(as_uuid=True), sa.ForeignKey("subscriptions.id"), nullable=True),
        sa.Column("invoice_number", sa.String(30), nullable=False, unique=True),  # FAC-2026-0001
        sa.Column("status", sa.String(20), nullable=False, server_default="DRAFT"),
        # DRAFT, SENT, PAID, OVERDUE, CANCELLED, REFUNDED
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("currency", sa.String(5), nullable=False, server_default="XOF"),
        sa.Column("tax_rate", sa.Numeric(5, 2), nullable=False, server_default="18.0"),  # TVA UEMOA 18%
        sa.Column("tax_amount", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("total_amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("due_date", sa.Date, nullable=True),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("period_start", sa.Date, nullable=True),
        sa.Column("period_end", sa.Date, nullable=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("billing_details", JSON, nullable=True),     # snapshot adresse/NIF client
        sa.Column("pdf_path", sa.String(500), nullable=True),
        sa.Column("reminder_sent_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("last_reminder_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_invoices_tenant_id", "invoices", ["tenant_id"])
    op.create_index("ix_invoices_status", "invoices", ["status"])
    op.create_index("ix_invoices_due_date", "invoices", ["due_date"])

    # ── payments ─────────────────────────────────────────────────────────────
    op.create_table(
        "payments",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.Column("invoice_id", UUID(as_uuid=True), sa.ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        # CinetPay
        sa.Column("cinetpay_transaction_id", sa.String(100), nullable=True, unique=True),
        sa.Column("cinetpay_payment_token", sa.String(200), nullable=True),
        sa.Column("payment_method", sa.String(30), nullable=True),
        # ORANGE_MONEY, WAVE, MOOV_MONEY, CARD, BANK_TRANSFER
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("currency", sa.String(5), nullable=False, server_default="XOF"),
        sa.Column("status", sa.String(20), nullable=False, server_default="PENDING"),
        # PENDING, COMPLETED, FAILED, REFUNDED, CANCELLED
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failure_reason", sa.Text, nullable=True),
        sa.Column("raw_response", JSON, nullable=True),    # réponse brute CinetPay
        sa.Column("initiated_by", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
    )
    op.create_index("ix_payments_tenant_id", "payments", ["tenant_id"])
    op.create_index("ix_payments_invoice_id", "payments", ["invoice_id"])
    op.create_index("ix_payments_status", "payments", ["status"])
    op.create_index("ix_payments_cinetpay_tid", "payments", ["cinetpay_transaction_id"])


def downgrade() -> None:
    op.drop_table("payments")
    op.drop_table("invoices")
    op.drop_table("subscriptions")
    op.drop_table("subscription_plans")
