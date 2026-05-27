from sqlalchemy import Column, String, Text, Integer, Boolean, Date, Numeric, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


class CRMClient(Base):
    __tablename__ = "crm_clients"

    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="SET NULL"), nullable=True, index=True)
    assigned_to = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    company_name = Column(String(200), nullable=False)
    rccm = Column(String(50), nullable=True)
    nif = Column(String(50), nullable=True)
    sector = Column(String(100), nullable=True)
    country = Column(String(50), nullable=False, default="BF")
    city = Column(String(100), nullable=True)
    address = Column(Text, nullable=True)
    website = Column(String(200), nullable=True)

    lifecycle_status = Column(String(20), nullable=False, default="PROSPECT")
    pipeline_stage = Column(String(20), nullable=False, default="PROSPECT")
    deal_value = Column(Numeric(14, 2), nullable=True)
    expected_close_date = Column(Date, nullable=True)
    source = Column(String(50), nullable=True)
    lost_reason = Column(Text, nullable=True)

    health_score = Column(Integer, nullable=True)
    tags = Column(JSON, nullable=True)
    notes = Column(Text, nullable=True)
    trial_ends_at = Column(String, nullable=True)
    last_contact_at = Column(String, nullable=True)

    contacts = relationship("CRMContact", back_populates="client", cascade="all, delete-orphan")
    activities = relationship("ActivityLog", back_populates="client", cascade="all, delete-orphan")


class CRMContact(Base):
    __tablename__ = "crm_contacts"

    crm_client_id = Column(UUID(as_uuid=True), ForeignKey("crm_clients.id", ondelete="CASCADE"), nullable=False, index=True)
    full_name = Column(String(200), nullable=False)
    role = Column(String(100), nullable=True)
    email = Column(String(200), nullable=True)
    phone = Column(String(30), nullable=True)
    is_primary = Column(Boolean, nullable=False, default=False)

    client = relationship("CRMClient", back_populates="contacts")


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    crm_client_id = Column(UUID(as_uuid=True), ForeignKey("crm_clients.id", ondelete="CASCADE"), nullable=False, index=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    activity_type = Column(String(30), nullable=False)  # CALL, EMAIL, MEETING, DEMO, NOTE, RELANCE
    subject = Column(String(300), nullable=True)
    body = Column(Text, nullable=True)
    outcome = Column(String(100), nullable=True)
    next_action = Column(Text, nullable=True)
    next_action_date = Column(Date, nullable=True)
    duration_minutes = Column(Integer, nullable=True)

    client = relationship("CRMClient", back_populates="activities")
