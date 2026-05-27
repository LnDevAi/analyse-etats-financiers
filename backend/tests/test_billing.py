"""Tests unitaires pour les schemas billing et le générateur de factures PDF."""
import pytest
from decimal import Decimal
from datetime import date
from uuid import uuid4
from pydantic import ValidationError

from app.schemas.billing import (
    SubscriptionCreate, SubscriptionUpgrade, PaymentInitiate,
    BillingDashboard, RevenueStat,
)
from app.services.invoice_generator import generate_invoice_pdf


# ── SubscriptionCreate ────────────────────────────────────────────────────────

class TestSubscriptionCreate:
    def test_defaults(self):
        plan_id = uuid4()
        s = SubscriptionCreate(plan_id=plan_id)
        assert s.billing_cycle == "MONTHLY"
        assert s.plan_id == plan_id

    def test_yearly_cycle(self):
        s = SubscriptionCreate(plan_id=uuid4(), billing_cycle="YEARLY")
        assert s.billing_cycle == "YEARLY"

    def test_missing_plan_id_raises(self):
        with pytest.raises(ValidationError):
            SubscriptionCreate()


# ── SubscriptionUpgrade ───────────────────────────────────────────────────────

class TestSubscriptionUpgrade:
    def test_plan_id_required(self):
        with pytest.raises(ValidationError):
            SubscriptionUpgrade()

    def test_optional_billing_cycle(self):
        u = SubscriptionUpgrade(plan_id=uuid4())
        assert u.billing_cycle is None

    def test_with_cycle(self):
        u = SubscriptionUpgrade(plan_id=uuid4(), billing_cycle="YEARLY")
        assert u.billing_cycle == "YEARLY"


# ── PaymentInitiate ───────────────────────────────────────────────────────────

class TestPaymentInitiate:
    def test_valid(self):
        p = PaymentInitiate(invoice_id=uuid4(), payment_method="ORANGE_MONEY")
        assert p.payment_method == "ORANGE_MONEY"
        assert p.return_url is None

    def test_with_urls(self):
        p = PaymentInitiate(
            invoice_id=uuid4(),
            payment_method="WAVE",
            return_url="https://app.edefence.tech/billing",
            notify_url="https://api.edefence.tech/api/v1/billing/payments/webhook",
        )
        assert p.return_url.startswith("https://")

    def test_missing_invoice_id_raises(self):
        with pytest.raises(ValidationError):
            PaymentInitiate(payment_method="CARD")


# ── BillingDashboard ──────────────────────────────────────────────────────────

class TestBillingDashboard:
    def test_valid(self):
        d = BillingDashboard(
            mrr=75000.0,
            arr=900000.0,
            active_subscriptions=12,
            trial_subscriptions=3,
            overdue_invoices=1,
            overdue_amount=75000.0,
            revenue_by_month=[
                RevenueStat(month="Mai 2026", revenue=225000.0, invoices_count=3, paid_count=3)
            ],
            subscriptions_by_plan={"Starter": 5, "Pro": 7},
        )
        assert d.mrr == 75000.0
        assert d.arr == 900000.0
        assert len(d.revenue_by_month) == 1

    def test_zero_values_valid(self):
        d = BillingDashboard(
            mrr=0, arr=0, active_subscriptions=0, trial_subscriptions=0,
            overdue_invoices=0, overdue_amount=0,
            revenue_by_month=[], subscriptions_by_plan={},
        )
        assert d.mrr == 0


# ── InvoicePDF ────────────────────────────────────────────────────────────────

class TestInvoiceGenerator:
    def _generate(self, **kwargs) -> bytes:
        defaults = dict(
            invoice_number="FAC-2026-0001",
            issue_date=date(2026, 5, 27),
            due_date=date(2026, 6, 10),
            period_start=date(2026, 5, 1),
            period_end=date(2026, 5, 31),
            client_name="ONG AIDE Burkina",
            client_nif="123456789",
            client_address="Ouagadougou, Burkina Faso",
            plan_name="Pro",
            billing_cycle="MONTHLY",
            amount_ht=Decimal("63559"),
            tax_rate=Decimal("18"),
            tax_amount=Decimal("11441"),
            total_amount=Decimal("75000"),
            currency="XOF",
        )
        defaults.update(kwargs)
        return generate_invoice_pdf(**defaults)

    def test_returns_bytes(self):
        pdf = self._generate()
        assert isinstance(pdf, bytes)

    def test_pdf_header_present(self):
        pdf = self._generate()
        assert pdf[:4] == b"%PDF"

    def test_non_empty(self):
        pdf = self._generate()
        assert len(pdf) > 5000

    def test_enterprise_plan(self):
        pdf = self._generate(plan_name="Enterprise", billing_cycle="YEARLY")
        assert isinstance(pdf, bytes)
        assert len(pdf) > 0

    def test_different_invoice_number(self):
        pdf1 = self._generate(invoice_number="FAC-2026-0001")
        pdf2 = self._generate(invoice_number="FAC-2026-0099")
        assert pdf1 != pdf2

    def test_zero_tax(self):
        pdf = self._generate(tax_rate=Decimal("0"), tax_amount=Decimal("0"), total_amount=Decimal("75000"))
        assert isinstance(pdf, bytes)


# ── CinetPay status mapping ───────────────────────────────────────────────────

class TestCinetpayMapping:
    def test_accepted_maps_to_completed(self):
        from app.services.cinetpay_client import map_cinetpay_status
        assert map_cinetpay_status("ACCEPTED") == "COMPLETED"

    def test_refused_maps_to_failed(self):
        from app.services.cinetpay_client import map_cinetpay_status
        assert map_cinetpay_status("REFUSED") == "FAILED"

    def test_pending_maps_to_pending(self):
        from app.services.cinetpay_client import map_cinetpay_status
        assert map_cinetpay_status("PENDING") == "PENDING"

    def test_unknown_maps_to_pending(self):
        from app.services.cinetpay_client import map_cinetpay_status
        assert map_cinetpay_status("UNKNOWN_STATUS") == "PENDING"

    def test_cancelled_maps_to_cancelled(self):
        from app.services.cinetpay_client import map_cinetpay_status
        assert map_cinetpay_status("CANCELLED") == "CANCELLED"
