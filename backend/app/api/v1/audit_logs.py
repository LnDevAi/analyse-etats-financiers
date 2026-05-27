from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from datetime import datetime

from app.core.database import get_db
from app.core.security import ROLES
from app.middleware.auth import get_current_user
from app.models.user import User, UserRole
from app.models.audit_log import AuditLog
from fastapi import HTTPException

router = APIRouter(prefix="/audit-logs", tags=["Logs d'audit"])


@router.get("/")
async def list_audit_logs(
    limit: int = Query(50, le=200),
    action: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if ROLES.get(current_user.role.value, 0) < ROLES.get(UserRole.CHEF_MISSION.value, 0):
        raise HTTPException(status_code=403, detail="Rôle Chef de mission requis")

    query = select(AuditLog).where(AuditLog.tenant_id == current_user.tenant_id)
    if action:
        query = query.where(AuditLog.action == action.upper())

    query = query.order_by(AuditLog.created_at.desc()).limit(limit)
    result = await db.execute(query)
    logs = result.scalars().all()

    return [
        {
            "id": str(log.id),
            "action": log.action,
            "resource_type": log.resource_type,
            "resource_id": log.resource_id,
            "user_id": str(log.user_id) if log.user_id else None,
            "ip_address": log.ip_address,
            "result": log.result,
            "extra_data": log.extra_data,
            "created_at": log.created_at.isoformat(),
        }
        for log in logs
    ]
