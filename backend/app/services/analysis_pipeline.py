"""
Pipeline d'analyse complète : orchestration de tous les modules IA.
"""
import asyncio
from typing import Optional, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.models.analysis import Analysis, AnalysisStatus, RiskLevel, Anomaly
from app.models.document import Document, DocumentStatus
from app.services.fec_parser import parse_fec, validate_partie_double
from app.services.benford import run_benford_analysis
from app.services.isolation_forest import run_isolation_forest
from app.services.analytical_review import run_analytical_review
from app.services.cycle_audit import run_cycle_ventes, run_cycle_tresorerie
from app.services.risk_scorer import compute_risk_score
from app.services.report_generator import generate_ai_synthesis, generate_word_report, generate_excel_report
from app.services.anonymizer import anonymize_fec_dataframe
from app.core.config import settings
import logging
import os

logger = logging.getLogger(__name__)


async def run_full_analysis(
    analysis_id: UUID,
    document_id: UUID,
    tenant_id: UUID,
    db: AsyncSession,
    previous_document_id: Optional[UUID] = None,
):
    """Exécute le pipeline IA complet sur un document FEC."""
    try:
        # Récupérer l'analyse et le document
        result = await db.execute(select(Analysis).where(Analysis.id == analysis_id))
        analysis = result.scalar_one_or_none()
        if not analysis:
            return

        doc_result = await db.execute(select(Document).where(Document.id == document_id))
        document = doc_result.scalar_one_or_none()
        if not document:
            return

        # Marquer comme en cours
        analysis.status = AnalysisStatus.RUNNING
        await db.commit()

        # Lire le fichier
        storage_path = document.storage_path
        if not os.path.exists(storage_path):
            raise FileNotFoundError(f"Fichier introuvable : {storage_path}")

        with open(storage_path, "rb") as f:
            content = f.read()

        # Parser le FEC
        df, meta = parse_fec(content)
        fiscal_year = document.fiscal_year
        entity_name = document.entity_name or "Entité inconnue"

        # Anonymisation NLP avant traitement IA
        df, anon_stats = anonymize_fec_dataframe(df)
        logger.info(f"Anonymisation : {anon_stats['total_substitutions']} substitutions sur {anon_stats['columns_processed']}")

        # Module 1 : Vérification intrinsèque
        intrinsic_check = validate_partie_double(df)

        # Module 2 : Loi de Benford
        benford_result = None
        for col in ["Debit", "Credit"]:
            if col in df.columns:
                benford_result = run_benford_analysis(df, col)
                if benford_result.get("sufficient_data"):
                    break

        # Module 3 : Isolation Forest
        isolation_forest_result = run_isolation_forest(df)

        # Module 4 : Revue analytique (avec N-1 si disponible)
        df_previous = None
        if previous_document_id:
            prev_doc_result = await db.execute(select(Document).where(Document.id == previous_document_id))
            prev_document = prev_doc_result.scalar_one_or_none()
            if prev_document and os.path.exists(prev_document.storage_path):
                with open(prev_document.storage_path, "rb") as f:
                    prev_content = f.read()
                df_previous, _ = parse_fec(prev_content)
                df_previous, _ = anonymize_fec_dataframe(df_previous)
                logger.info(f"FEC N-1 chargé pour la revue analytique ({len(df_previous)} lignes)")
        analytical_review = run_analytical_review(df, df_previous)

        # Module 5 : Cycle Ventes
        cycle_ventes_result = run_cycle_ventes(df, fiscal_year)

        # Module 6 : Cycle Trésorerie
        cycle_tresorerie_result = run_cycle_tresorerie(df)

        # Calcul du score de risque global
        scoring = compute_risk_score(
            intrinsic_check=intrinsic_check,
            benford_result=benford_result,
            isolation_forest_result=isolation_forest_result,
            analytical_review=analytical_review,
            cycle_ventes_result=cycle_ventes_result,
            cycle_tresorerie_result=cycle_tresorerie_result,
        )

        # Génération synthèse IA
        ai_synthesis = await generate_ai_synthesis(
            risk_score=scoring["global_score"],
            risk_level=scoring["risk_level"],
            entity_name=entity_name,
            fiscal_year=fiscal_year,
            benford=benford_result,
            isolation_forest=isolation_forest_result,
            analytical_review=analytical_review,
            cycle_ventes=cycle_ventes_result,
            cycle_tresorerie=cycle_tresorerie_result,
        )

        # Génération rapports Word + Excel
        output_dir = os.path.join(settings.UPLOAD_DIR, str(tenant_id), "reports")
        analysis_dict = {
            "risk_score": scoring["global_score"],
            "risk_level": scoring["risk_level"],
            "intrinsic_check": intrinsic_check,
            "benford_result": benford_result,
            "isolation_forest_result": isolation_forest_result,
            "analytical_review": analytical_review,
            "cycle_ventes_result": cycle_ventes_result,
            "cycle_tresorerie_result": cycle_tresorerie_result,
            "ai_synthesis": ai_synthesis,
        }
        docx_path = generate_word_report(analysis_dict, entity_name, fiscal_year, output_dir)
        xlsx_path = generate_excel_report(analysis_dict, entity_name, fiscal_year, output_dir)

        # Mise à jour de l'analyse
        analysis.status = AnalysisStatus.COMPLETED
        analysis.risk_score = scoring["global_score"]
        analysis.risk_level = RiskLevel(scoring["risk_level"])
        analysis.intrinsic_check = intrinsic_check
        analysis.benford_result = benford_result
        analysis.isolation_forest_result = isolation_forest_result
        analysis.analytical_review = analytical_review
        analysis.cycle_ventes_result = cycle_ventes_result
        analysis.cycle_tresorerie_result = cycle_tresorerie_result
        analysis.ai_synthesis = ai_synthesis
        analysis.docx_report_path = docx_path
        analysis.xlsx_report_path = xlsx_path

        # Créer les anomalies détectées
        await _create_anomalies(db, analysis_id, tenant_id, isolation_forest_result, cycle_tresorerie_result, cycle_ventes_result, benford_result)

        await db.commit()
        logger.info(f"Analyse {analysis_id} terminée — score {scoring['global_score']}")

    except Exception as e:
        logger.error(f"Erreur pipeline analyse {analysis_id}: {e}", exc_info=True)
        result = await db.execute(select(Analysis).where(Analysis.id == analysis_id))
        analysis = result.scalar_one_or_none()
        if analysis:
            analysis.status = AnalysisStatus.FAILED
            analysis.error_message = str(e)[:500]
            await db.commit()


async def _create_anomalies(
    db: AsyncSession,
    analysis_id: UUID,
    tenant_id: UUID,
    isolation_forest: Optional[Dict],
    tresorerie: Optional[Dict],
    ventes: Optional[Dict],
    benford: Optional[Dict],
):
    anomalies = []

    if isolation_forest and isolation_forest.get("sufficient_data"):
        for entry in isolation_forest.get("top_anomalies", [])[:10]:
            anomalies.append(Anomaly(
                analysis_id=analysis_id,
                tenant_id=tenant_id,
                module="ISOLATION_FOREST",
                severity=RiskLevel(isolation_forest.get("risk_level", "ORANGE")),
                description=f"Écriture atypique détectée (score={entry.get('anomaly_score', 0):.3f})",
                affected_account=entry.get("account"),
                amount=entry.get("debit") or entry.get("credit"),
                details=entry,
            ))

    if tresorerie and tresorerie.get("suspicious_transactions"):
        for tx in tresorerie["suspicious_transactions"][:10]:
            anomalies.append(Anomaly(
                analysis_id=analysis_id,
                tenant_id=tenant_id,
                module="CYCLE_TRESORERIE",
                severity=RiskLevel(tx.get("severity", "ORANGE")),
                description=f"Transaction suspecte — {tx.get('type', '')}",
                affected_account=tx.get("account"),
                amount=tx.get("amount"),
                details=tx,
            ))

    if benford and benford.get("risk_level") in ["ORANGE", "ROUGE"]:
        anomalies.append(Anomaly(
            analysis_id=analysis_id,
            tenant_id=tenant_id,
            module="BENFORD",
            severity=RiskLevel(benford.get("risk_level", "ORANGE")),
            description=benford.get("interpretation", "Déviation loi de Benford"),
            details={"conformity_score": benford.get("conformity_score"), "p_value": benford.get("p_value")},
        ))

    for a in anomalies:
        db.add(a)
