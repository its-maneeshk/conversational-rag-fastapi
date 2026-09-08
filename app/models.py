from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from pydantic import BaseModel, Field

# ==========================================
# 1. SQLAlchemy Database Models (Tables)
# ==========================================

class DocumentMetadata(Base):
    """Database table to store metadata of uploaded documents."""
    __tablename__ = "document_metadata"

    id: int = Column(Integer, primary_key=True, index=True)
    filename: str = Column(String, nullable=False)
    strategy: str = Column(String, nullable=False)
    chunk_count: int = Column(Integer, nullable=False)
    created_at: datetime = Column(DateTime, default=datetime.utcnow)


class InterviewBooking(Base):
    """Database table to store interview bookings detected by LLM."""
    __tablename__ = "interview_bookings"

    id: int = Column(Integer, primary_key=True, index=True)
    name: str = Column(String, nullable=False)
    email: str = Column(String, nullable=False)
    date: str = Column(String, nullable=False)
    time: str = Column(String, nullable=False)
    created_at: datetime = Column(DateTime, default=datetime.utcnow)


# ==========================================
# 2. Pydantic Schemas (API Data Validation)
# ==========================================

class IngestResponse(BaseModel):
    """Response schema for /ingest endpoint."""
    message: str
    filename: str
    strategy_used: str
    chunks_stored: int


class ChatRequest(BaseModel):
    """Request schema for /chat endpoint."""
    session_id: str = Field(..., description="Unique session ID for chat memory")
    query: str = Field(..., description="User query or message")


class ChatResponse(BaseModel):
    """Response schema for /chat endpoint."""
    session_id: str
    response: str
    booking_detected: bool = False