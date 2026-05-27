from fastapi import APIRouter
from app.api.v1 import auth, documents, analysis, users, tenants, cross_check, audit_logs, ag_analysis, crm, billing

router = APIRouter()
router.include_router(auth.router)
router.include_router(documents.router)
router.include_router(analysis.router)
router.include_router(users.router)
router.include_router(tenants.router)
router.include_router(cross_check.router)
router.include_router(audit_logs.router)
router.include_router(ag_analysis.router)
router.include_router(crm.router)
router.include_router(billing.router)
