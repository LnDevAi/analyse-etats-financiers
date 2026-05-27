"""
Client CinetPay — initiation de paiement et vérification de statut.
Docs: https://docs.cinetpay.com
"""
import httpx
import uuid
import logging
from typing import Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

CINETPAY_BASE = "https://api-checkout.cinetpay.com/v2"

# Méthodes de paiement CinetPay par canal
PAYMENT_CHANNELS = {
    "ORANGE_MONEY": "OM",
    "MOOV_MONEY": "FLOOZ",
    "WAVE": "WAVE",
    "CARD": "CREDIT_CARD",
    "BANK_TRANSFER": None,  # manuel — pas de redirection CinetPay
}


async def initiate_payment(
    amount: int,
    transaction_id: str,
    description: str,
    customer_name: str,
    customer_email: str,
    currency: str = "XOF",
    return_url: Optional[str] = None,
    notify_url: Optional[str] = None,
    payment_method: Optional[str] = None,
) -> dict:
    """
    Initie un paiement via CinetPay.
    Retourne {"payment_url": ..., "payment_token": ...} en cas de succès.
    """
    channel = PAYMENT_CHANNELS.get(payment_method or "", None)

    payload = {
        "apikey": settings.CINETPAY_API_KEY,
        "site_id": settings.CINETPAY_SITE_ID,
        "transaction_id": transaction_id,
        "amount": amount,
        "currency": currency,
        "description": description,
        "return_url": return_url or settings.FRONTEND_URL + "/account/billing",
        "notify_url": notify_url or settings.BACKEND_URL + "/api/v1/payments/webhook",
        "customer_name": customer_name,
        "customer_email": customer_email,
        "lang": "fr",
    }
    if channel:
        payload["channels"] = channel

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(f"{CINETPAY_BASE}/payment", json=payload)
        resp.raise_for_status()
        data = resp.json()

    if data.get("code") != "201":
        raise ValueError(f"CinetPay erreur: {data.get('message', 'unknown')}")

    return {
        "payment_url": data["data"]["payment_url"],
        "payment_token": data["data"]["payment_token"],
    }


async def check_payment_status(transaction_id: str) -> dict:
    """
    Vérifie le statut d'une transaction CinetPay.
    Retourne {"status": "ACCEPTED"|"REFUSED"|"PENDING", ...}
    """
    payload = {
        "apikey": settings.CINETPAY_API_KEY,
        "site_id": settings.CINETPAY_SITE_ID,
        "transaction_id": transaction_id,
    }
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(f"{CINETPAY_BASE}/payment/check", json=payload)
        resp.raise_for_status()
        data = resp.json()

    code = data.get("data", {}).get("status", "REFUSED")
    return {
        "status": code,  # ACCEPTED, REFUSED, PENDING
        "operator_id": data.get("data", {}).get("operator_id"),
        "payment_method": data.get("data", {}).get("payment_method"),
        "raw": data,
    }


def map_cinetpay_status(cinetpay_status: str) -> str:
    """Traduit le statut CinetPay en statut interne."""
    return {
        "ACCEPTED": "COMPLETED",
        "REFUSED": "FAILED",
        "PENDING": "PENDING",
        "CANCELLED": "CANCELLED",
    }.get(cinetpay_status, "PENDING")
