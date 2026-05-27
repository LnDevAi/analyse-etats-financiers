from sqlalchemy import Column, String, Integer, Float, Enum, ForeignKey, UUID, Text, JSON, Boolean
from sqlalchemy.orm import relationship
import enum
from app.core.database import Base


class AnalysisStatus(str, enum.Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class RiskLevel(str, enum.Enum):
    VERT = "VERT"
    ORANGE = "ORANGE"
    ROUGE = "ROUGE"


class Analysis(Base):
    __tablename__ = "analyses"

    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    triggered_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    status = Column(Enum(AnalysisStatus), nullable=False, default=AnalysisStatus.PENDING)

    # Score global 0-100
    risk_score = Column(Float, nullable=True)
    risk_level = Column(Enum(RiskLevel), nullable=True)

    # Résultats modules IA
    intrinsic_check = Column(JSON, nullable=True)
    benford_result = Column(JSON, nullable=True)
    isolation_forest_result = Column(JSON, nullable=True)
    cross_check_result = Column(JSON, nullable=True)
    analytical_review = Column(JSON, nullable=True)
    cycle_ventes_result = Column(JSON, nullable=True)
    cycle_tresorerie_result = Column(JSON, nullable=True)

    # Rapport IA généré
    ai_synthesis = Column(Text, nullable=True)
    ai_report_general = Column(Text, nullable=True)

    # Export paths
    docx_report_path = Column(String(512), nullable=True)
    xlsx_report_path = Column(String(512), nullable=True)

    error_message = Column(Text, nullable=True)

    tenant = relationship("Tenant", back_populates="analyses")
    document = relationship("Document", back_populates="analyses")
    anomalies = relationship("Anomaly", back_populates="analysis", lazy="select")


class Anomaly(Base):
    __tablename__ = "anomalies"

    analysis_id = Column(UUID(as_uuid=True), ForeignKey("analyses.id", ondelete="CASCADE"), nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)

    module = Column(String(100), nullable=False)
    severity = Column(Enum(RiskLevel), nullable=False, default=RiskLevel.ORANGE)
    description = Column(Text, nullable=False)
    affected_account = Column(String(50), nullable=True)
    amount = Column(Float, nullable=True)
    details = Column(JSON, nullable=True)

    analysis = relationship("Analysis", back_populates="anomalies")
