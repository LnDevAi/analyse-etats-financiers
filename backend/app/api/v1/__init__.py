from fastapi import APIRouter
from app.api.v1 import auth, documents, analysis, users, tenants

router = APIRouter()
router.include_router(auth.router)
router.include_router(documents.router)
router.include_router(analysis.router)
router.include_router(users.router)
router.include_router(tenants.router)
