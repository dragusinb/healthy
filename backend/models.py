from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from .database import Base
import datetime

class Provider(Base):
    __tablename__ = "providers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True) # e.g., "regina_maria", "synevo"
    username = Column(String)
    # Store encrypted password/token
    encrypted_credentials = Column(String)
    
class BiomarkerAlias(Base):
    __tablename__ = "biomarker_aliases"
    
    id = Column(Integer, primary_key=True, index=True)
    alias = Column(String, unique=True, index=True) # The raw string found in PDF
    standardized_name = Column(String, nullable=True) # The official key in BIOMARKER_KNOWLEDGE
    is_ignored = Column(Boolean, default=False) # If True, parser skips this forever
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    provider_id = Column(Integer, ForeignKey("providers.id"))
    filename = Column(String)
    file_path = Column(String) # Local path in /data/raw
    file_type = Column(String) # PDF, IMG, HTML
    document_date = Column(DateTime)
    upload_date = Column(DateTime, default=datetime.datetime.utcnow)
    category = Column(String) # analysis, consult, imaging
    
    provider = relationship("Provider")

class TestResult(Base):
    __tablename__ = "test_results"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"))
    test_name = Column(String, index=True)
    value = Column(String)
    unit = Column(String)
    reference_range = Column(String)
    flags = Column(String) # HIGH, LOW, NORMAL
    category = Column(String) # Biochimie, Hematologie, etc
    
    document = relationship("Document")
