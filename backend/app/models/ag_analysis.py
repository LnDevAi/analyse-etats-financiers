from sqlalchemy import Column, String, Float, Enum, ForeignKey, UUID, Text, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.analysis import AnalysisStatus, RiskLevel


class AGAnalysis(Base):
    __tablename__ = "ag_analyses"

    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    triggered_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Document FEC de référence
    fec_document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)

    # Documents AG optionnels
    budget_document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=True)
    social_document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=True)
    marches_document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=True)
    activites_document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=True)

    status = Column(Enum(AnalysisStatus), nullable=False, default=AnalysisStatus.PENDING)

    # Résultats des 4 modules
    budget_comparison = Column(JSON, nullable=True)
    masse_salariale_check = Column(JSON, nullable=True)
    marches_check = Column(JSON, nullable=True)
    activites_check = Column(JSON, nullable=True)

    # Score global
    coherence_score = Column(Float, nullable=True)
    risk_level = Column(Enum(RiskLevel), nullable=True)
    ai_synthesis = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)

    tenant = relationship("Tenant")
    fec_document = relationship("Document", foreign_keys=[fec_document_id])
