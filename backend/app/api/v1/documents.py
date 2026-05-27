from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import os
import uuid
import aiofiles
from typing import Optional, List

from app.core.database import get_db
from app.core.config import settings
from app.middleware.auth import get_current_user
from app.middleware.audit_logger import log_action
from app.models.user import User, UserRole
from app.models.document import Document, DocumentType, DocumentStatus
from app.models.analysis import Analysis, AnalysisStatus

router = APIRouter(prefix="/documents", tags=["Documents"])

ALLOWED_MIMES = {
    "text/plain", "text/csv", "application/octet-stream",
    "application/pdf",
    "application/vnd.ms-excel",
}


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    document_type: DocumentType = Form(DocumentType.FEC),
    fiscal_year: Optional[int] = Form(None),
    entity_name: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    content = await file.read()
    size_mb = len(content) / 1024 / 1024

    if size_mb > settings.MAX_UPLOAD_SIZE_MB:
        raise HTTPException(status_code=413, detail=f"Fichier trop volumineux (max {settings.MAX_UPLOAD_SIZE_MB} MB)")

    tenant_dir = os.path.join(settings.UPLOAD_DIR, str(current_user.tenant_id), "documents")
    os.makedirs(tenant_dir, exist_ok=True)

    filename = f"{uuid.uuid4().hex}_{file.filename}"
    filepath = os.path.join(tenant_dir, filename)

    async with aiofiles.open(filepath, "wb") as f:
        await f.write(content)

    doc = Document(
        tenant_id=current_user.tenant_id,
        uploaded_by=current_user.id,
        original_filename=file.filename,
        storage_path=filepath,
        document_type=document_type,
        file_size_bytes=len(content),
        mime_type=file.content_type or "application/octet-stream",
        status=DocumentStatus.READY,
        fiscal_year=fiscal_year,
        entity_name=entity_name,
    )
    db.add(doc)
    await log_action(db, "DOCUMENT_UPLOAD", user=current_user, resource_type="Document", resource_id=file.filename)
    await db.commit()
    await db.refresh(doc)

    return {
        "id": str(doc.id),
        "original_filename": doc.original_filename,
        "document_type": doc.document_type,
        "file_size_bytes": doc.file_size_bytes,
        "status": doc.status,
        "fiscal_year": doc.fiscal_year,
        "entity_name": doc.entity_name,
        "created_at": doc.created_at.isoformat(),
    }


@router.get("/")
async def list_documents(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Document)
        .where(Document.tenant_id == current_user.tenant_id)
        .order_by(Document.created_at.desc())
        .limit(50)
    )
    docs = result.scalars().all()
    return [
        {
            "id": str(d.id),
            "original_filename": d.original_filename,
            "document_type": d.document_type,
            "file_size_bytes": d.file_size_bytes,
            "status": d.status,
            "fiscal_year": d.fiscal_year,
            "entity_name": d.entity_name,
            "created_at": d.created_at.isoformat(),
        }
        for d in docs
    ]


@router.delete("/{document_id}")
async def delete_document(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.core.security import ROLES
    if ROLES.get(current_user.role.value, 0) < ROLES.get(UserRole.CHEF_MISSION.value, 0):
        raise HTTPException(status_code=403, detail="Rôle Chef de mission requis")

    result = await db.execute(
        select(Document).where(
            Document.id == document_id,
            Document.tenant_id == current_user.tenant_id,
        )
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document introuvable")

    if os.path.exists(doc.storage_path):
        os.remove(doc.storage_path)

    await db.delete(doc)
    await log_action(db, "DOCUMENT_DELETE", user=current_user, resource_type="Document", resource_id=str(document_id))
    await db.commit()
    return {"message": "Document supprimé"}
