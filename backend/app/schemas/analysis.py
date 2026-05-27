from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from app.models.analysis import AnalysisStatus, RiskLevel


class AnalysisCreate(BaseModel):
    document_id: UUID


class AnomalyOut(BaseModel):
    id: UUID
    module: str
    severity: RiskLevel
    description: str
    affected_account: Optional[str]
    amount: Optional[float]
    details: Optional[Dict[str, Any]]

    class Config:
        from_attributes = True


class AnalysisOut(BaseModel):
    id: UUID
    document_id: UUID
    status: AnalysisStatus
    risk_score: Optional[float]
    risk_level: Optional[RiskLevel]
    intrinsic_check: Optional[Dict[str, Any]]
    benford_result: Optional[Dict[str, Any]]
    isolation_forest_result: Optional[Dict[str, Any]]
    cross_check_result: Optional[Dict[str, Any]]
    analytical_review: Optional[Dict[str, Any]]
    cycle_ventes_result: Optional[Dict[str, Any]]
    cycle_tresorerie_result: Optional[Dict[str, Any]]
    ai_synthesis: Optional[str]
    anomalies: List[AnomalyOut] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DashboardStats(BaseModel):
    total_analyses: int
    analyses_this_month: int
    avg_risk_score: float
    high_risk_count: int
    medium_risk_count: int
    low_risk_count: int
    recent_analyses: List[AnalysisOut]
