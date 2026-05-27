"""
Endpoints CRM — gestion des clients, contacts, activités.
Accès réservé aux administrateurs.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import uuid
from typing import List, Optional

from app.core.database import get_db
from app.middleware.auth import get_current_user, require_role
from app.middleware.audit_logger import log_action
from app.models.user import User
from app.models.crm import CRMClient, CRMContact, ActivityLog
from app.schemas.crm import (
    CRMClientCreate, CRMClientUpdate, CRMClientOut,
    CRMContactCreate, CRMContactOut,
    ActivityLogCreate, ActivityLogOut,
)

router = APIRouter(prefix="/crm", tags=["CRM"])


# ── Clients ───────────────────────────────────────────────────────────────────

@router.get("/clients", response_model=List[CRMClientOut])
async def list_clients(
    stage: Optional[str] = Query(None),
    lifecycle: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    current_user: User = Depends(require_role("ASSOCIE")),
    db: AsyncSession = Depends(get_db),
):
    q = select(CRMClient).order_by(CRMClient.updated_at.desc())
    if stage:
        q = q.where(CRMClient.pipeline_stage == stage)
    if lifecycle:
        q = q.where(CRMClient.lifecycle_status == lifecycle)
    if search:
        q = q.where(CRMClient.company_name.ilike(f"%{search}%"))
    q = q.limit(limit).offset(offset)
    result = await db.execute(q)
    return result.scalars().all()


@router.post("/clients", response_model=CRMClientOut)
async def create_client(
    body: CRMClientCreate,
    current_user: User = Depends(require_role("ASSOCIE")),
    db: AsyncSession = Depends(get_db),
):
    client = CRMClient(**body.model_dump())
    db.add(client)
    await log_action(db, "CRM_CLIENT_CREATED", user=current_user,
                     resource_type="CRMClient", resource_id=body.company_name)
    await db.commit()
    await db.refresh(client)
    return client


@router.get("/clients/{client_id}", response_model=CRMClientOut)
async def get_client(
    client_id: uuid.UUID,
    current_user: User = Depends(require_role("ASSOCIE")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(CRMClient).where(CRMClient.id == client_id))
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(404, "Client introuvable")
    return client


@router.patch("/clients/{client_id}", response_model=CRMClientOut)
async def update_client(
    client_id: uuid.UUID,
    body: CRMClientUpdate,
    current_user: User = Depends(require_role("ASSOCIE")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(CRMClient).where(CRMClient.id == client_id))
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(404, "Client introuvable")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(client, field, value)
    await log_action(db, "CRM_CLIENT_UPDATED", user=current_user,
                     resource_type="CRMClient", resource_id=str(client_id))
    await db.commit()
    await db.refresh(client)
    return client


@router.delete("/clients/{client_id}", status_code=204)
async def delete_client(
    client_id: uuid.UUID,
    current_user: User = Depends(require_role("ASSOCIE")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(CRMClient).where(CRMClient.id == client_id))
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(404, "Client introuvable")
    await db.delete(client)
    await db.commit()


# ── Pipeline stats ────────────────────────────────────────────────────────────

@router.get("/pipeline/stats")
async def pipeline_stats(
    current_user: User = Depends(require_role("ASSOCIE")),
    db: AsyncSession = Depends(get_db),
):
    stages = ["PROSPECT", "QUALIFIÉ", "DÉMO", "NÉGOCIATION", "GAGNÉ", "PERDU"]
    result = await db.execute(
        select(CRMClient.pipeline_stage, func.count(CRMClient.id), func.sum(CRMClient.deal_value))
        .group_by(CRMClient.pipeline_stage)
    )
    rows = result.all()
    by_stage = {s: {"count": 0, "deal_value": 0} for s in stages}
    for stage, count, val in rows:
        if stage in by_stage:
            by_stage[stage] = {"count": count, "deal_value": float(val or 0)}
    return by_stage


# ── Contacts ──────────────────────────────────────────────────────────────────

@router.post("/clients/{client_id}/contacts", response_model=CRMContactOut)
async def add_contact(
    client_id: uuid.UUID,
    body: CRMContactCreate,
    current_user: User = Depends(require_role("ASSOCIE")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(CRMClient).where(CRMClient.id == client_id))
    if not result.scalar_one_or_none():
        raise HTTPException(404, "Client introuvable")
    contact = CRMContact(crm_client_id=client_id, **body.model_dump())
    db.add(contact)
    await db.commit()
    await db.refresh(contact)
    return contact


@router.delete("/contacts/{contact_id}", status_code=204)
async def delete_contact(
    contact_id: uuid.UUID,
    current_user: User = Depends(require_role("ASSOCIE")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(CRMContact).where(CRMContact.id == contact_id))
    contact = result.scalar_one_or_none()
    if not contact:
        raise HTTPException(404, "Contact introuvable")
    await db.delete(contact)
    await db.commit()


# ── Activities ────────────────────────────────────────────────────────────────

@router.get("/clients/{client_id}/activities", response_model=List[ActivityLogOut])
async def list_activities(
    client_id: uuid.UUID,
    current_user: User = Depends(require_role("ASSOCIE")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ActivityLog)
        .where(ActivityLog.crm_client_id == client_id)
        .order_by(ActivityLog.created_at.desc())
        .limit(100)
    )
    return result.scalars().all()


@router.post("/clients/{client_id}/activities", response_model=ActivityLogOut)
async def add_activity(
    client_id: uuid.UUID,
    body: ActivityLogCreate,
    current_user: User = Depends(require_role("ASSOCIE")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(CRMClient).where(CRMClient.id == client_id))
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(404, "Client introuvable")
    activity = ActivityLog(
        crm_client_id=client_id,
        created_by=current_user.id,
        **body.model_dump(),
    )
    db.add(activity)
    # Mise à jour last_contact_at
    from datetime import datetime, timezone
    client.last_contact_at = datetime.now(timezone.utc).isoformat()
    await db.commit()
    await db.refresh(activity)
    return activity
