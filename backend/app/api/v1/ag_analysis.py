"""
Endpoints pour l'analyse comparative des documents AG.
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid, os, logging
from typing import List

from app.core.database import get_db
from app.middleware.auth import get_current_user
from app.middleware.audit_logger import log_action
from app.models.user import User
from app.models.document import Document
from app.models.ag_analysis import AGAnalysis
from app.models.analysis import AnalysisStatus, RiskLevel
from app.schemas.ag_analysis import AGAnalysisCreate, AGAnalysisOut
from app.services.fec_parser import parse_fec
from app.services.anonymizer import anonymize_fec_dataframe
from app.services.ag_document_analyzer import run_ag_comparative_analysis

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ag-analyses", tags=["Analyse AG"])


async def _load_doc_content(db: AsyncSession, doc_id, tenant_id) -> tuple:
    """Charge le contenu binaire d'un document et son nom de fichier."""
    if not doc_id:
        return None, ""
    result = await db.execute(
        select(Document).where(Document.id == doc_id, Document.tenant_id == tenant_id)
    )
    doc = result.scalar_one_or_none()
    if not doc or not os.path.exists(doc.storage_path):
        return None, ""
    with open(doc.storage_path, "rb") as f:
        return f.read(), doc.original_filename


async def _run_ag_pipeline(ag_id: uuid.UUID, tenant_id: uuid.UUID, db: AsyncSession):
    """Pipeline AG exécuté en arrière-plan."""
    try:
        result = await db.execute(select(AGAnalysis).where(AGAnalysis.id == ag_id))
        ag = result.scalar_one_or_none()
        if not ag:
            return

        ag.status = AnalysisStatus.RUNNING
        await db.commit()

        # Charger le FEC
        fec_content, _ = await _load_doc_content(db, ag.fec_document_id, tenant_id)
        if not fec_content:
            raise FileNotFoundError("FEC introuvable")
        df_fec, _ = parse_fec(fec_content)
        df_fec, _ = anonymize_fec_dataframe(df_fec)

        # Charger les documents AG
        budget_content, budget_fn = await _load_doc_content(db, ag.budget_document_id, tenant_id)
        social_content, social_fn = await _load_doc_content(db, ag.social_document_id, tenant_id)
        marches_content, marches_fn = await _load_doc_content(db, ag.marches_document_id, tenant_id)
        activites_content, activites_fn = await _load_doc_content(db, ag.activites_document_id, tenant_id)

        # Exécuter l'analyse
        analysis_results = run_ag_comparative_analysis(
            df_fec=df_fec,
            budget_content=budget_content,
            budget_filename=budget_fn or "budget.csv",
            social_content=social_content,
            social_filename=social_fn or "bilan_social.xlsx",
            marches_content=marches_content,
            marches_filename=marches_fn or "marches.xlsx",
            activites_content=activites_content,
            activites_filename=activites_fn or "rapport_activites.pdf",
        )

        global_result = analysis_results.pop("global", {})
        ag.budget_comparison = analysis_results.get("budget_execution")
        ag.masse_salariale_check = analysis_results.get("masse_salariale")
        ag.marches_check = analysis_results.get("marches")
        ag.activites_check = analysis_results.get("activites")
        ag.coherence_score = global_result.get("coherence_score")
        ag.risk_level = RiskLevel(global_result.get("risk_level", "VERT"))
        ag.ai_synthesis = global_result.get("interpretation")
        ag.status = AnalysisStatus.COMPLETED

        await db.commit()
        logger.info(f"Analyse AG {ag_id} terminée — score {ag.coherence_score}")

    except Exception as e:
        logger.error(f"Erreur pipeline AG {ag_id}: {e}", exc_info=True)
        result = await db.execute(select(AGAnalysis).where(AGAnalysis.id == ag_id))
        ag = result.scalar_one_or_none()
        if ag:
            ag.status = AnalysisStatus.FAILED
            ag.error_message = str(e)[:500]
            await db.commit()


@router.post("/", response_model=AGAnalysisOut)
async def create_ag_analysis(
    body: AGAnalysisCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Vérifier le FEC
    fec_check = await db.execute(
        select(Document).where(
            Document.id == body.fec_document_id,
            Document.tenant_id == current_user.tenant_id,
        )
    )
    if not fec_check.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Document FEC introuvable")

    # Vérifier les documents AG si fournis
    for field, doc_id in [
        ("budget", body.budget_document_id),
        ("bilan_social", body.social_document_id),
        ("marches", body.marches_document_id),
        ("activites", body.activites_document_id),
    ]:
        if doc_id:
            check = await db.execute(
                select(Document).where(
                    Document.id == doc_id,
                    Document.tenant_id == current_user.tenant_id,
                )
            )
            if not check.scalar_one_or_none():
                raise HTTPException(status_code=404, detail=f"Document {field} introuvable")

    ag = AGAnalysis(
        tenant_id=current_user.tenant_id,
        triggered_by=current_user.id,
        fec_document_id=body.fec_document_id,
        budget_document_id=body.budget_document_id,
        social_document_id=body.social_document_id,
        marches_document_id=body.marches_document_id,
        activites_document_id=body.activites_document_id,
        status=AnalysisStatus.PENDING,
    )
    db.add(ag)
    await log_action(db, "AG_ANALYSIS_STARTED", user=current_user,
                     resource_type="AGAnalysis", resource_id=str(body.fec_document_id))
    await db.commit()
    await db.refresh(ag)

    background_tasks.add_task(_run_ag_pipeline, ag.id, current_user.tenant_id, db)
    return ag


@router.get("/", response_model=List[AGAnalysisOut])
async def list_ag_analyses(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(AGAnalysis)
        .where(AGAnalysis.tenant_id == current_user.tenant_id)
        .order_by(AGAnalysis.created_at.desc())
        .limit(20)
    )
    return result.scalars().all()


@router.get("/{ag_id}", response_model=AGAnalysisOut)
async def get_ag_analysis(
    ag_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(AGAnalysis).where(
            AGAnalysis.id == ag_id,
            AGAnalysis.tenant_id == current_user.tenant_id,
        )
    )
    ag = result.scalar_one_or_none()
    if not ag:
        raise HTTPException(status_code=404, detail="Analyse AG introuvable")
    return ag
