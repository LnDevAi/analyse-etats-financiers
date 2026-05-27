"""
Endpoints billing — abonnements, factures, paiements CinetPay.
"""
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from datetime import datetime, timezone, date, timedelta
from decimal import Decimal
import uuid, io, logging, json
from typing import List

from app.core.database import get_db
from app.core.config import settings
from app.middleware.auth import get_current_user, require_role
from app.middleware.audit_logger import log_action
from app.models.user import User
from app.models.billing import SubscriptionPlan, Subscription, Invoice, Payment
from app.schemas.billing import (
    SubscriptionPlanOut, SubscriptionOut, SubscriptionCreate, SubscriptionUpgrade,
    InvoiceOut, PaymentInitiate, PaymentOut, PaymentInitiateResponse, BillingDashboard,
)
from app.services import cinetpay_client
from app.services.invoice_generator import generate_invoice_pdf

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/billing", tags=["Billing"])

TAX_RATE = Decimal("18.0")  # TVA UEMOA


def _compute_tax(amount_ht: Decimal) -> tuple[Decimal, Decimal]:
    tax = (amount_ht * TAX_RATE / 100).quantize(Decimal("0.01"))
    return tax, amount_ht + tax


async def _next_invoice_number(db: AsyncSession) -> str:
    year = datetime.now().year
    result = await db.execute(
        select(func.count(Invoice.id)).where(
            Invoice.invoice_number.like(f"FAC-{year}-%")
        )
    )
    count = result.scalar() or 0
    return f"FAC-{year}-{count + 1:04d}"


# ── Plans ─────────────────────────────────────────────────────────────────────

@router.get("/plans", response_model=List[SubscriptionPlanOut])
async def list_plans(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(SubscriptionPlan)
        .where(SubscriptionPlan.is_active == True)
        .order_by(SubscriptionPlan.sort_order)
    )
    return result.scalars().all()


# ── Subscription (tenant) ─────────────────────────────────────────────────────

@router.get("/subscription", response_model=SubscriptionOut)
async def get_my_subscription(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Subscription).where(Subscription.tenant_id == current_user.tenant_id)
    )
    sub = result.scalar_one_or_none()
    if not sub:
        raise HTTPException(404, "Aucun abonnement actif")
    return sub


@router.post("/subscription", response_model=SubscriptionOut)
async def create_subscription(
    body: SubscriptionCreate,
    current_user: User = Depends(require_role("ASSOCIE")),
    db: AsyncSession = Depends(get_db),
):
    plan_res = await db.execute(select(SubscriptionPlan).where(SubscriptionPlan.id == body.plan_id))
    plan = plan_res.scalar_one_or_none()
    if not plan:
        raise HTTPException(404, "Plan introuvable")

    now = datetime.now(timezone.utc)
    trial_end = now + timedelta(days=plan.trial_days)
    sub = Subscription(
        tenant_id=current_user.tenant_id,
        plan_id=body.plan_id,
        billing_cycle=body.billing_cycle,
        status="TRIAL",
        trial_ends_at=trial_end.isoformat(),
    )
    db.add(sub)
    await log_action(db, "SUBSCRIPTION_CREATED", user=current_user,
                     resource_type="Subscription", resource_id=str(body.plan_id))
    await db.commit()
    await db.refresh(sub)
    return sub


@router.patch("/subscription/upgrade", response_model=SubscriptionOut)
async def upgrade_subscription(
    body: SubscriptionUpgrade,
    current_user: User = Depends(require_role("ASSOCIE")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Subscription).where(Subscription.tenant_id == current_user.tenant_id)
    )
    sub = result.scalar_one_or_none()
    if not sub:
        raise HTTPException(404, "Aucun abonnement actif")
    plan_res = await db.execute(select(SubscriptionPlan).where(SubscriptionPlan.id == body.plan_id))
    if not plan_res.scalar_one_or_none():
        raise HTTPException(404, "Plan introuvable")
    sub.plan_id = body.plan_id
    if body.billing_cycle:
        sub.billing_cycle = body.billing_cycle
    await log_action(db, "SUBSCRIPTION_UPGRADED", user=current_user,
                     resource_type="Subscription", resource_id=str(body.plan_id))
    await db.commit()
    await db.refresh(sub)
    return sub


# ── Invoices ──────────────────────────────────────────────────────────────────

@router.get("/invoices", response_model=List[InvoiceOut])
async def list_invoices(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Invoice)
        .where(Invoice.tenant_id == current_user.tenant_id)
        .order_by(Invoice.created_at.desc())
        .limit(50)
    )
    return result.scalars().all()


@router.get("/invoices/{invoice_id}/pdf")
async def download_invoice_pdf(
    invoice_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Invoice).where(
            Invoice.id == invoice_id,
            Invoice.tenant_id == current_user.tenant_id,
        )
    )
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(404, "Facture introuvable")

    billing = invoice.billing_details or {}
    sub_res = await db.execute(select(Subscription).where(Subscription.id == invoice.subscription_id))
    sub = sub_res.scalar_one_or_none()
    plan_name = "—"
    if sub:
        plan_res = await db.execute(select(SubscriptionPlan).where(SubscriptionPlan.id == sub.plan_id))
        plan = plan_res.scalar_one_or_none()
        plan_name = plan.display_name if plan else "—"

    pdf_bytes = generate_invoice_pdf(
        invoice_number=invoice.invoice_number,
        issue_date=invoice.created_at.date(),
        due_date=invoice.due_date or invoice.created_at.date(),
        period_start=invoice.period_start or invoice.created_at.date(),
        period_end=invoice.period_end or invoice.created_at.date(),
        client_name=billing.get("company_name", "Client"),
        client_nif=billing.get("nif", ""),
        client_address=billing.get("address", ""),
        plan_name=plan_name,
        billing_cycle=sub.billing_cycle if sub else "MONTHLY",
        amount_ht=Decimal(str(invoice.amount)),
        tax_rate=Decimal(str(invoice.tax_rate)),
        tax_amount=Decimal(str(invoice.tax_amount)),
        total_amount=Decimal(str(invoice.total_amount)),
    )
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{invoice.invoice_number}.pdf"'},
    )


# ── Payments ──────────────────────────────────────────────────────────────────

@router.post("/payments/initiate", response_model=PaymentInitiateResponse)
async def initiate_payment(
    body: PaymentInitiate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    inv_res = await db.execute(
        select(Invoice).where(
            Invoice.id == body.invoice_id,
            Invoice.tenant_id == current_user.tenant_id,
        )
    )
    invoice = inv_res.scalar_one_or_none()
    if not invoice:
        raise HTTPException(404, "Facture introuvable")
    if invoice.status == "PAID":
        raise HTTPException(400, "Facture déjà payée")

    transaction_id = str(uuid.uuid4()).replace("-", "")[:20].upper()

    try:
        cp_result = await cinetpay_client.initiate_payment(
            amount=int(invoice.total_amount),
            transaction_id=transaction_id,
            description=f"Abonnement E-DÉFENCE — {invoice.invoice_number}",
            customer_name=current_user.full_name,
            customer_email=current_user.email,
            return_url=body.return_url,
            notify_url=body.notify_url,
            payment_method=body.payment_method,
        )
    except Exception as e:
        logger.error(f"CinetPay initiate error: {e}")
        raise HTTPException(502, "Erreur lors de l'initiation du paiement")

    payment = Payment(
        invoice_id=invoice.id,
        tenant_id=current_user.tenant_id,
        cinetpay_transaction_id=transaction_id,
        cinetpay_payment_token=cp_result.get("payment_token"),
        payment_method=body.payment_method,
        amount=invoice.total_amount,
        currency=invoice.currency,
        status="PENDING",
        initiated_by=current_user.id,
    )
    db.add(payment)
    await db.commit()
    await db.refresh(payment)

    return PaymentInitiateResponse(
        payment_id=payment.id,
        payment_url=cp_result["payment_url"],
        transaction_id=transaction_id,
    )


@router.post("/payments/webhook")
async def cinetpay_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """Webhook CinetPay — appelé par CinetPay après confirmation de paiement."""
    try:
        data = await request.json()
    except Exception:
        data = dict(await request.form())

    transaction_id = data.get("cpm_trans_id") or data.get("transaction_id")
    if not transaction_id:
        return Response(status_code=400)

    result = await db.execute(
        select(Payment).where(Payment.cinetpay_transaction_id == transaction_id)
    )
    payment = result.scalar_one_or_none()
    if not payment:
        return Response(status_code=404)

    try:
        status_data = await cinetpay_client.check_payment_status(transaction_id)
    except Exception as e:
        logger.error(f"Webhook check error: {e}")
        return Response(status_code=502)

    internal_status = cinetpay_client.map_cinetpay_status(status_data["status"])
    payment.status = internal_status
    payment.raw_response = status_data["raw"]
    payment.payment_method = status_data.get("payment_method") or payment.payment_method

    if internal_status == "COMPLETED":
        payment.completed_at = datetime.now(timezone.utc).isoformat()
        inv_res = await db.execute(select(Invoice).where(Invoice.id == payment.invoice_id))
        invoice = inv_res.scalar_one_or_none()
        if invoice:
            invoice.status = "PAID"
            invoice.paid_at = datetime.now(timezone.utc).isoformat()
        # Activer l'abonnement si TRIAL ou PAST_DUE
        sub_res = await db.execute(
            select(Subscription).where(Subscription.tenant_id == payment.tenant_id)
        )
        sub = sub_res.scalar_one_or_none()
        if sub and sub.status in ("TRIAL", "PAST_DUE", "SUSPENDED"):
            sub.status = "ACTIVE"
            now = datetime.now(timezone.utc)
            sub.current_period_start = now.isoformat()
            sub.current_period_end = (now + timedelta(days=30)).isoformat()

    await db.commit()
    return {"status": "ok"}


@router.get("/payments", response_model=List[PaymentOut])
async def list_payments(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Payment)
        .where(Payment.tenant_id == current_user.tenant_id)
        .order_by(Payment.created_at.desc())
        .limit(50)
    )
    return result.scalars().all()


# ── Dashboard admin ───────────────────────────────────────────────────────────

@router.get("/dashboard", response_model=BillingDashboard)
async def billing_dashboard(
    current_user: User = Depends(require_role("ASSOCIE")),
    db: AsyncSession = Depends(get_db),
):
    # MRR = somme montants mensuels des abonnements ACTIVE
    active_res = await db.execute(
        select(func.count(Subscription.id), func.sum(SubscriptionPlan.price_monthly))
        .join(SubscriptionPlan, Subscription.plan_id == SubscriptionPlan.id)
        .where(Subscription.status == "ACTIVE")
    )
    active_count, mrr_sum = active_res.one()
    mrr = float(mrr_sum or 0)

    trial_res = await db.execute(
        select(func.count(Subscription.id)).where(Subscription.status == "TRIAL")
    )
    trial_count = trial_res.scalar() or 0

    overdue_res = await db.execute(
        select(func.count(Invoice.id), func.sum(Invoice.total_amount))
        .where(Invoice.status == "OVERDUE")
    )
    overdue_count, overdue_amount = overdue_res.one()

    # Revenus 6 derniers mois
    revenue_rows = []
    for i in range(5, -1, -1):
        month_start = (datetime.now() - timedelta(days=30 * i)).replace(day=1)
        month_end = (month_start + timedelta(days=32)).replace(day=1)
        r = await db.execute(
            select(func.count(Invoice.id), func.sum(Invoice.total_amount))
            .where(
                Invoice.status == "PAID",
                Invoice.paid_at >= month_start.isoformat(),
                Invoice.paid_at < month_end.isoformat(),
            )
        )
        cnt, total = r.one()
        revenue_rows.append({
            "month": month_start.strftime("%b %Y"),
            "revenue": float(total or 0),
            "invoices_count": cnt or 0,
            "paid_count": cnt or 0,
        })

    # Par plan
    plan_rows = await db.execute(
        select(SubscriptionPlan.display_name, func.count(Subscription.id))
        .join(Subscription, Subscription.plan_id == SubscriptionPlan.id)
        .where(Subscription.status.in_(["ACTIVE", "TRIAL"]))
        .group_by(SubscriptionPlan.display_name)
    )
    by_plan = {name: count for name, count in plan_rows.all()}

    return BillingDashboard(
        mrr=mrr,
        arr=mrr * 12,
        active_subscriptions=active_count or 0,
        trial_subscriptions=trial_count,
        overdue_invoices=overdue_count or 0,
        overdue_amount=float(overdue_amount or 0),
        revenue_by_month=revenue_rows,
        subscriptions_by_plan=by_plan,
    )
