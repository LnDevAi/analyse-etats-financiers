from sqlalchemy import Column, String, Boolean, Enum
from sqlalchemy.orm import relationship
import enum
from app.core.database import Base


class TenantType(str, enum.Enum):
    CABINET_EXPERTISE = "CABINET_EXPERTISE"
    ADMINISTRATION_FISCALE = "ADMINISTRATION_FISCALE"
    BANQUE = "BANQUE"


class Tenant(Base):
    __tablename__ = "tenants"

    name = Column(String(255), nullable=False)
    type = Column(Enum(TenantType), nullable=False, default=TenantType.CABINET_EXPERTISE)
    siret = Column(String(50), nullable=True)
    email_contact = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    schema_name = Column(String(63), unique=True, nullable=False)

    users = relationship("User", back_populates="tenant", lazy="select")
    documents = relationship("Document", back_populates="tenant", lazy="select")
    analyses = relationship("Analysis", back_populates="tenant", lazy="select")
