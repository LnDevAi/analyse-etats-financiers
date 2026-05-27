from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
import re

from app.core.database import get_db
from app.core.security import hash_password
from app.middleware.audit_logger import log_action
from app.models.tenant import Tenant, TenantType
from app.models.user import User, UserRole

router = APIRouter(prefix="/tenants", tags=["Tenants"])


class TenantRegisterRequest(BaseModel):
    tenant_name: str
    tenant_type: TenantType = TenantType.CABINET_EXPERTISE
    admin_email: str
    admin_full_name: str
    admin_password: str


@router.post("/register")
async def register_tenant(
    body: TenantRegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    """Inscription d'un nouveau cabinet/institution — crée le tenant + admin."""
    existing = await db.execute(select(User).where(User.email == body.admin_email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email déjà utilisé")

    schema_name = re.sub(r"[^a-z0-9_]", "_", body.tenant_name.lower())[:50]
    schema_name = f"t_{schema_name}"

    tenant = Tenant(
        name=body.tenant_name,
        type=body.tenant_type,
        email_contact=body.admin_email,
        schema_name=schema_name,
    )
    db.add(tenant)
    await db.flush()

    admin = User(
        email=body.admin_email,
        full_name=body.admin_full_name,
        hashed_password=hash_password(body.admin_password),
        role=UserRole.ASSOCIE,
        tenant_id=tenant.id,
    )
    db.add(admin)
    await log_action(db, "TENANT_REGISTER", resource_type="Tenant", resource_id=body.tenant_name)
    await db.commit()
    await db.refresh(tenant)

    return {
        "message": "Inscription réussie",
        "tenant_id": str(tenant.id),
        "tenant_name": tenant.name,
        "admin_email": admin.email,
    }
