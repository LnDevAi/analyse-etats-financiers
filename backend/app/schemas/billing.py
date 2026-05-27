from pydantic import BaseModel
from typing import Optional, List, Any
from uuid import UUID
from datetime import datetime, date
from decimal import Decimal


# ── Plans ─────────────────────────────────────────────────────────────────────

class SubscriptionPlanOut(BaseModel):
    id: UUID
    name: str
    display_name: str
    price_monthly: Decimal
    price_yearly: Optional[Decimal]
    max_analyses: Optional[int]
    max_users: Optional[int]
    max_documents: Optional[int]
    trial_days: int
    features: Optional[Any]
    is_active: bool
    sort_order: int

    class Config:
        from_attributes = True


# ── Subscriptions ─────────────────────────────────────────────────────────────

class SubscriptionOut(BaseModel):
    id: UUID
    tenant_id: UUID
    plan_id: UUID
    billing_cycle: str
    status: str
    trial_ends_at: Optional[str]
    current_period_start: Optional[str]
    current_period_end: Optional[str]
    cancel_at_period_end: bool
    analyses_used: int
    documents_used: int
    created_at: datetime
    plan: Optional[SubscriptionPlanOut] = None

    class Config:
        from_attributes = True


class SubscriptionCreate(BaseModel):
    plan_id: UUID
    billing_cycle: str = "MONTHLY"


class SubscriptionUpgrade(BaseModel):
    plan_id: UUID
    billing_cycle: Optional[str] = None


# ── Invoices ──────────────────────────────────────────────────────────────────

class InvoiceOut(BaseModel):
    id: UUID
    tenant_id: UUID
    invoice_number: str
    status: str
    amount: Decimal
    currency: str
    tax_rate: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    due_date: Optional[date]
    paid_at: Optional[str]
    period_start: Optional[date]
    period_end: Optional[date]
    description: Optional[str]
    pdf_path: Optional[str]
    reminder_sent_count: int
    created_at: datetime

    class Config:
        from_attributes = True


# ── Payments ──────────────────────────────────────────────────────────────────

class PaymentInitiate(BaseModel):
    invoice_id: UUID
    payment_method: str  # ORANGE_MONEY, WAVE, MOOV_MONEY, CARD, BANK_TRANSFER
    return_url: Optional[str] = None
    notify_url: Optional[str] = None


class PaymentOut(BaseModel):
    id: UUID
    invoice_id: UUID
    tenant_id: UUID
    cinetpay_transaction_id: Optional[str]
    payment_method: Optional[str]
    amount: Decimal
    currency: str
    status: str
    completed_at: Optional[str]
    failure_reason: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class PaymentInitiateResponse(BaseModel):
    payment_id: UUID
    payment_url: str
    transaction_id: str


# ── Dashboard ─────────────────────────────────────────────────────────────────

class RevenueStat(BaseModel):
    month: str
    revenue: float
    invoices_count: int
    paid_count: int


class BillingDashboard(BaseModel):
    mrr: float
    arr: float
    active_subscriptions: int
    trial_subscriptions: int
    overdue_invoices: int
    overdue_amount: float
    revenue_by_month: List[RevenueStat]
    subscriptions_by_plan: dict
