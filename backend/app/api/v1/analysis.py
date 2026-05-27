from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import uuid
from typing import List
from datetime import datetime, timedelta, timezone

from app.core.database import get_db
from app.middleware.auth import get_current_user
from app.middleware.audit_logger import log_action
from app.models.user import User
from app.models.document import Document
from app.models.analysis import Analysis, AnalysisStatus, Anomaly
from app.schemas.analysis import AnalysisCreate, AnalysisOut, DashboardStats
from app.services.analysis_pipeline import run_full_analysis

router = APIRouter(prefix="/analyses", tags=["Analyses IA"])


@router.post("/", response_model=AnalysisOut)
async def create_analysis(
    body: AnalysisCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    doc_result = await db.execute(
        select(Document).where(
            Document.id == body.document_id,
            Document.tenant_id == current_user.tenant_id,
        )
    )
    document = doc_result.scalar_one_or_none()
    if not document:
        raise HTTPException(status_code=404, detail="Document introuvable")

    # Vérifier le document N-1 si fourni
    if body.previous_document_id:
        prev_doc_result = await db.execute(
            select(Document).where(
                Document.id == body.previous_document_id,
                Document.tenant_id == current_user.tenant_id,
            )
        )
        if not prev_doc_result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Document N-1 introuvable")

    analysis = Analysis(
        tenant_id=current_user.tenant_id,
        document_id=body.document_id,
        triggered_by=current_user.id,
        status=AnalysisStatus.PENDING,
    )
    db.add(analysis)
    await log_action(db, "ANALYSIS_STARTED", user=current_user, resource_type="Analysis", resource_id=str(body.document_id))
    await db.commit()
    await db.refresh(analysis)

    background_tasks.add_task(
        run_full_analysis,
        analysis.id,
        body.document_id,
        current_user.tenant_id,
        db,
        body.previous_document_id,
    )

    return analysis


@router.get("/", response_model=List[AnalysisOut])
async def list_analyses(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Analysis)
        .where(Analysis.tenant_id == current_user.tenant_id)
        .order_by(Analysis.created_at.desc())
        .limit(20)
    )
    return result.scalars().all()


@router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    total = await db.execute(
        select(func.count()).where(Analysis.tenant_id == current_user.tenant_id)
    )
    total_count = total.scalar() or 0

    this_month = await db.execute(
        select(func.count()).where(
            Analysis.tenant_id == current_user.tenant_id,
            Analysis.created_at >= month_start,
        )
    )
    this_month_count = this_month.scalar() or 0

    avg = await db.execute(
        select(func.avg(Analysis.risk_score)).where(
            Analysis.tenant_id == current_user.tenant_id,
            Analysis.status == AnalysisStatus.COMPLETED,
        )
    )
    avg_score = float(avg.scalar() or 0)

    completed = await db.execute(
        select(Analysis)
        .where(
            Analysis.tenant_id == current_user.tenant_id,
            Analysis.status == AnalysisStatus.COMPLETED,
        )
    )
    completed_list = completed.scalars().all()

    high_risk = sum(1 for a in completed_list if a.risk_level and a.risk_level.value == "ROUGE")
    medium_risk = sum(1 for a in completed_list if a.risk_level and a.risk_level.value == "ORANGE")
    low_risk = sum(1 for a in completed_list if a.risk_level and a.risk_level.value == "VERT")

    recent = await db.execute(
        select(Analysis)
        .where(Analysis.tenant_id == current_user.tenant_id)
        .order_by(Analysis.created_at.desc())
        .limit(5)
    )

    return DashboardStats(
        total_analyses=total_count,
        analyses_this_month=this_month_count,
        avg_risk_score=round(avg_score, 1),
        high_risk_count=high_risk,
        medium_risk_count=medium_risk,
        low_risk_count=low_risk,
        recent_analyses=recent.scalars().all(),
    )


@router.get("/{analysis_id}", response_model=AnalysisOut)
async def get_analysis(
    analysis_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Analysis).where(
            Analysis.id == analysis_id,
            Analysis.tenant_id == current_user.tenant_id,
        )
    )
    analysis = result.scalar_one_or_none()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analyse introuvable")
    return analysis


@router.get("/{analysis_id}/report/docx")
async def download_docx(
    analysis_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Analysis).where(
            Analysis.id == analysis_id,
            Analysis.tenant_id == current_user.tenant_id,
        )
    )
    analysis = result.scalar_one_or_none()
    if not analysis or not analysis.docx_report_path:
        raise HTTPException(status_code=404, detail="Rapport Word non disponible")

    await log_action(db, "REPORT_DOWNLOAD", user=current_user, resource_type="Analysis", resource_id=str(analysis_id), extra_data={"format": "docx"})
    await db.commit()
    return FileResponse(analysis.docx_report_path, media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document", filename="rapport_audit.docx")


@router.get("/{analysis_id}/report/xlsx")
async def download_xlsx(
    analysis_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Analysis).where(
            Analysis.id == analysis_id,
            Analysis.tenant_id == current_user.tenant_id,
        )
    )
    analysis = result.scalar_one_or_none()
    if not analysis or not analysis.xlsx_report_path:
        raise HTTPException(status_code=404, detail="Rapport Excel non disponible")

    await log_action(db, "REPORT_DOWNLOAD", user=current_user, resource_type="Analysis", resource_id=str(analysis_id), extra_data={"format": "xlsx"})
    await db.commit()
    return FileResponse(analysis.xlsx_report_path, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", filename="rapport_audit.xlsx")
