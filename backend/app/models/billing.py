from sqlalchemy import Column, String, Text, Integer, Boolean, Date, Numeric, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


class SubscriptionPlan(Base):
    __tablename__ = "subscription_plans"

    name = Column(String(50), nullable=False, unique=True)
    display_name = Column(String(100), nullable=False)
    price_monthly = Column(Numeric(12, 2), nullable=False)
    price_yearly = Column(Numeric(12, 2), nullable=True)
    max_analyses = Column(Integer, nullable=True)
    max_users = Column(Integer, nullable=True)
    max_documents = Column(Integer, nullable=True)
    trial_days = Column(Integer, nullable=False, default=14)
    features = Column(JSON, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    sort_order = Column(Integer, nullable=False, default=0)

    subscriptions = relationship("Subscription", back_populates="plan")


class Subscription(Base):
    __tablename__ = "subscriptions"

    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    plan_id = Column(UUID(as_uuid=True), ForeignKey("subscription_plans.id"), nullable=False)
    billing_cycle = Column(String(10), nullable=False, default="MONTHLY")
    status = Column(String(20), nullable=False, default="TRIAL")
    trial_ends_at = Column(String, nullable=True)
    current_period_start = Column(String, nullable=True)
    current_period_end = Column(String, nullable=True)
    cancelled_at = Column(String, nullable=True)
    cancel_at_period_end = Column(Boolean, nullable=False, default=False)
    analyses_used = Column(Integer, nullable=False, default=0)
    documents_used = Column(Integer, nullable=False, default=0)

    plan = relationship("SubscriptionPlan", back_populates="subscriptions")
    invoices = relationship("Invoice", back_populates="subscription")


class Invoice(Base):
    __tablename__ = "invoices"

    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    subscription_id = Column(UUID(as_uuid=True), ForeignKey("subscriptions.id"), nullable=True)
    invoice_number = Column(String(30), nullable=False, unique=True)
    status = Column(String(20), nullable=False, default="DRAFT")
    amount = Column(Numeric(14, 2), nullable=False)
    currency = Column(String(5), nullable=False, default="XOF")
    tax_rate = Column(Numeric(5, 2), nullable=False, default=18.0)
    tax_amount = Column(Numeric(14, 2), nullable=False, default=0)
    total_amount = Column(Numeric(14, 2), nullable=False)
    due_date = Column(Date, nullable=True)
    paid_at = Column(String, nullable=True)
    period_start = Column(Date, nullable=True)
    period_end = Column(Date, nullable=True)
    description = Column(Text, nullable=True)
    billing_details = Column(JSON, nullable=True)
    pdf_path = Column(String(500), nullable=True)
    reminder_sent_count = Column(Integer, nullable=False, default=0)
    last_reminder_at = Column(String, nullable=True)

    subscription = relationship("Subscription", back_populates="invoices")
    payments = relationship("Payment", back_populates="invoice")


class Payment(Base):
    __tablename__ = "payments"

    invoice_id = Column(UUID(as_uuid=True), ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    cinetpay_transaction_id = Column(String(100), nullable=True, unique=True)
    cinetpay_payment_token = Column(String(200), nullable=True)
    payment_method = Column(String(30), nullable=True)
    amount = Column(Numeric(14, 2), nullable=False)
    currency = Column(String(5), nullable=False, default="XOF")
    status = Column(String(20), nullable=False, default="PENDING")
    completed_at = Column(String, nullable=True)
    failure_reason = Column(Text, nullable=True)
    raw_response = Column(JSON, nullable=True)
    initiated_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    invoice = relationship("Invoice", back_populates="payments")
