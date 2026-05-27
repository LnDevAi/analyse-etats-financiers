from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime


class AGAnalysisCreate(BaseModel):
    fec_document_id: UUID
    budget_document_id: Optional[UUID] = None
    social_document_id: Optional[UUID] = None
    marches_document_id: Optional[UUID] = None
    activites_document_id: Optional[UUID] = None


class AGAnalysisOut(BaseModel):
    id: UUID
    fec_document_id: UUID
    budget_document_id: Optional[UUID]
    social_document_id: Optional[UUID]
    marches_document_id: Optional[UUID]
    activites_document_id: Optional[UUID]
    status: str
    coherence_score: Optional[float]
    risk_level: Optional[str]
    budget_comparison: Optional[Dict[str, Any]]
    masse_salariale_check: Optional[Dict[str, Any]]
    marches_check: Optional[Dict[str, Any]]
    activites_check: Optional[Dict[str, Any]]
    ai_synthesis: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
