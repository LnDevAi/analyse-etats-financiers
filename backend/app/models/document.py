from sqlalchemy import Column, String, Integer, Enum, ForeignKey, UUID, Text, Boolean
from sqlalchemy.orm import relationship
import enum
from app.core.database import Base


class DocumentType(str, enum.Enum):
    FEC = "FEC"
    LIASSE_FISCALE_PDF = "LIASSE_FISCALE_PDF"
    BILAN_PDF = "BILAN_PDF"
    AUTRE = "AUTRE"


class DocumentStatus(str, enum.Enum):
    UPLOADED = "UPLOADED"
    PROCESSING = "PROCESSING"
    OCR_DONE = "OCR_DONE"
    ANONYMIZED = "ANONYMIZED"
    READY = "READY"
    ERROR = "ERROR"


class Document(Base):
    __tablename__ = "documents"

    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    original_filename = Column(String(255), nullable=False)
    storage_path = Column(String(512), nullable=False)
    document_type = Column(Enum(DocumentType), nullable=False, default=DocumentType.FEC)
    file_size_bytes = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=False)
    status = Column(Enum(DocumentStatus), nullable=False, default=DocumentStatus.UPLOADED)
    error_message = Column(Text, nullable=True)

    fiscal_year = Column(Integer, nullable=True)
    entity_name = Column(String(255), nullable=True)
    is_anonymized = Column(Boolean, default=False)

    extracted_text = Column(Text, nullable=True)

    tenant = relationship("Tenant", back_populates="documents")
    analyses = relationship("Analysis", back_populates="document", lazy="select")
