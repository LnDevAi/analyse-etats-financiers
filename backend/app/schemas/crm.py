from pydantic import BaseModel, EmailStr
from typing import Optional, List, Any
from uuid import UUID
from datetime import datetime, date


# ── Contacts ─────────────────────────────────────────────────────────────────

class CRMContactCreate(BaseModel):
    full_name: str
    role: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    is_primary: bool = False


class CRMContactOut(BaseModel):
    id: UUID
    full_name: str
    role: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    is_primary: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ── Activity Logs ─────────────────────────────────────────────────────────────

class ActivityLogCreate(BaseModel):
    activity_type: str  # CALL, EMAIL, MEETING, DEMO, NOTE, RELANCE
    subject: Optional[str] = None
    body: Optional[str] = None
    outcome: Optional[str] = None
    next_action: Optional[str] = None
    next_action_date: Optional[date] = None
    duration_minutes: Optional[int] = None


class ActivityLogOut(BaseModel):
    id: UUID
    activity_type: str
    subject: Optional[str]
    body: Optional[str]
    outcome: Optional[str]
    next_action: Optional[str]
    next_action_date: Optional[date]
    duration_minutes: Optional[int]
    created_by: Optional[UUID]
    created_at: datetime

    class Config:
        from_attributes = True


# ── CRM Clients ───────────────────────────────────────────────────────────────

class CRMClientCreate(BaseModel):
    company_name: str
    rccm: Optional[str] = None
    nif: Optional[str] = None
    sector: Optional[str] = None
    country: str = "BF"
    city: Optional[str] = None
    address: Optional[str] = None
    website: Optional[str] = None
    lifecycle_status: str = "PROSPECT"
    pipeline_stage: str = "PROSPECT"
    deal_value: Optional[float] = None
    expected_close_date: Optional[date] = None
    source: Optional[str] = None
    tags: Optional[List[str]] = None
    notes: Optional[str] = None
    assigned_to: Optional[UUID] = None
    tenant_id: Optional[UUID] = None


class CRMClientUpdate(BaseModel):
    company_name: Optional[str] = None
    rccm: Optional[str] = None
    nif: Optional[str] = None
    sector: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None
    website: Optional[str] = None
    lifecycle_status: Optional[str] = None
    pipeline_stage: Optional[str] = None
    deal_value: Optional[float] = None
    expected_close_date: Optional[date] = None
    source: Optional[str] = None
    lost_reason: Optional[str] = None
    health_score: Optional[int] = None
    tags: Optional[List[str]] = None
    notes: Optional[str] = None
    assigned_to: Optional[UUID] = None


class CRMClientOut(BaseModel):
    id: UUID
    tenant_id: Optional[UUID]
    assigned_to: Optional[UUID]
    company_name: str
    rccm: Optional[str]
    nif: Optional[str]
    sector: Optional[str]
    country: str
    city: Optional[str]
    address: Optional[str]
    website: Optional[str]
    lifecycle_status: str
    pipeline_stage: str
    deal_value: Optional[float]
    expected_close_date: Optional[date]
    source: Optional[str]
    lost_reason: Optional[str]
    health_score: Optional[int]
    tags: Optional[Any]
    notes: Optional[str]
    last_contact_at: Optional[str]
    created_at: datetime
    updated_at: datetime
    contacts: List[CRMContactOut] = []

    class Config:
        from_attributes = True
