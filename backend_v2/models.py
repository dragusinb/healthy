from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Float, Text
from sqlalchemy.orm import relationship
from backend_v2.database import Base
import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    linked_accounts = relationship("LinkedAccount", back_populates="user")
    documents = relationship("Document", back_populates="user")

class LinkedAccount(Base):
    __tablename__ = "linked_accounts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    provider_name = Column(String) # "Regina Maria" or "Synevo"
    username = Column(String)
    encrypted_password = Column(String) # In real app, encrypt this
    last_sync = Column(DateTime, nullable=True)
    status = Column(String, default="ACTIVE") 

    user = relationship("User", back_populates="linked_accounts")

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    filename = Column(String)
    file_path = Column(String)
    provider = Column(String) # "Regina Maria", "Synevo", "Upload"
    upload_date = Column(DateTime, default=datetime.datetime.utcnow)
    document_date = Column(DateTime, nullable=True)
    is_processed = Column(Boolean, default=False)
    
    user = relationship("User", back_populates="documents")
    results = relationship("TestResult", back_populates="document", cascade="all, delete-orphan")

class TestResult(Base):
    __tablename__ = "test_results"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"))
    test_name = Column(String, index=True)
    value = Column(String) # Store as string to handle "< 5" etc.
    numeric_value = Column(Float, nullable=True) # Parsed for graphing
    unit = Column(String, nullable=True)
    reference_range = Column(String, nullable=True)
    flags = Column(String, default="NORMAL") # NORMAL, HIGH, LOW
    category = Column(String, default="General")

    document = relationship("Document", back_populates="results")


class HealthReport(Base):
    __tablename__ = "health_reports"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    report_type = Column(String)  # "general", "cardiology", "endocrinology", etc.
    title = Column(String)
    summary = Column(Text)  # Brief overview
    findings = Column(Text)  # Detailed findings (JSON string)
    recommendations = Column(Text)  # AI recommendations (JSON string)
    risk_level = Column(String, default="normal")  # normal, attention, concern, urgent
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    biomarkers_analyzed = Column(Integer, default=0)

    user = relationship("User", back_populates="health_reports")


# Add relationship to User model
User.health_reports = relationship("HealthReport", back_populates="user")
