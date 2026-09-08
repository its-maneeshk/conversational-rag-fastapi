from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.config import settings

# Create engine for SQLite database
engine = create_engine(
    settings.SQLITE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.SQLITE_URL else {},
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for SQLAlchemy models
Base = declarative_base()

def get_db() -> Generator[Session, None, None]:
    """Dependency function to get a DB session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()