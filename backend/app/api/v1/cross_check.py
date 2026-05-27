from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from app.core.database import get_db
from app.core.config import settings
from app.middleware.auth import get_current_user
from app.middleware.audit_logger import log_action
from app.models.user import User
from app.models.document import Document
from app.services.cross_check import run_cross_check
import os

router = APIRouter(prefix="/cross-check", tags=["Cross-Checking"])


@router.post("/")
async def cross_check_documents(
    document_a_id: str = Form(...),
    document_b_id: str = Form(...),
    label_a: Optional[str] = Form("Document A (Impôts)"),
    label_b: Optional[str] = Form("Document B (Banque)"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Compare deux documents FEC de la même entité.
    Cas d'usage typique : bilan déposé aux impôts vs bilan présenté à la banque.
    """
    from uuid import UUID

    result_a = await db.execute(
        select(Document).where(
            Document.id == UUID(document_a_id),
            Document.tenant_id == current_user.tenant_id,
        )
    )
    doc_a = result_a.scalar_one_or_none()
    if not doc_a:
        raise HTTPException(status_code=404, detail="Document A introuvable")

    result_b = await db.execute(
        select(Document).where(
            Document.id == UUID(document_b_id),
            Document.tenant_id == current_user.tenant_id,
        )
    )
    doc_b = result_b.scalar_one_or_none()
    if not doc_b:
        raise HTTPException(status_code=404, detail="Document B introuvable")

    if not os.path.exists(doc_a.storage_path) or not os.path.exists(doc_b.storage_path):
        raise HTTPException(status_code=404, detail="Fichier(s) introuvable(s) sur le serveur")

    with open(doc_a.storage_path, "rb") as f:
        content_a = f.read()
    with open(doc_b.storage_path, "rb") as f:
        content_b = f.read()

    result = run_cross_check(content_a, content_b, label_a or "Document A", label_b or "Document B")

    await log_action(
        db, "CROSS_CHECK",
        user=current_user,
        resource_type="CrossCheck",
        resource_id=f"{document_a_id}|{document_b_id}",
    )
    await db.commit()

    return result
