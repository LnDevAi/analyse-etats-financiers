"""
Middleware de journalisation immuable — chaque action sensible est enregistrée.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.audit_log import AuditLog
from app.models.user import User
from typing import Optional, Dict, Any
from uuid import UUID


async def log_action(
    db: AsyncSession,
    action: str,
    user: Optional[User] = None,
    tenant_id: Optional[UUID] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    extra_data: Optional[Dict[str, Any]] = None,
    result: str = "SUCCESS",
):
    log = AuditLog(
        tenant_id=tenant_id or (user.tenant_id if user else None),
        user_id=user.id if user else None,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        ip_address=ip_address,
        user_agent=user_agent,
        extra_data=extra_data,
        result=result,
    )
    db.add(log)
    # Ne pas commit ici — le caller gère la transaction
