from sqlalchemy import Column, String, ForeignKey, UUID, Text, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base


class AuditLog(Base):
    """Logs immuables — jamais mis à jour, uniquement INSERT."""
    __tablename__ = "audit_logs"

    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="SET NULL"), nullable=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    action = Column(String(100), nullable=False)
    resource_type = Column(String(100), nullable=True)
    resource_id = Column(String(255), nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(512), nullable=True)
    extra_data = Column(JSON, nullable=True)
    result = Column(String(20), nullable=False, default="SUCCESS")

    user = relationship("User", back_populates="audit_logs")
