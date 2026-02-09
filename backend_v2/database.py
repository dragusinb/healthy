import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool

logger = logging.getLogger(__name__)

# Use DATABASE_URL from environment (Render provides this for PostgreSQL)
# Fall back to SQLite for local development
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    # Render uses postgres:// but SQLAlchemy needs postgresql://
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    # PostgreSQL with connection pooling for production
    engine = create_engine(
        DATABASE_URL,
        poolclass=QueuePool,
        pool_size=5,  # Number of connections to keep open
        max_overflow=10,  # Additional connections allowed when pool is full
        pool_timeout=30,  # Seconds to wait for connection from pool
        pool_recycle=1800,  # Recycle connections after 30 minutes
        pool_pre_ping=True,  # Test connections before using them
    )
    logger.info("Database engine created with connection pooling (pool_size=5, max_overflow=10)")
else:
    # Local development with SQLite (no pooling needed)
    DATABASE_URL = "sqlite:///./healthy_v2.db"
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
    logger.info("Database engine created for SQLite (local development)")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
