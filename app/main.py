from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db import Base, engine, get_db
from app.models import DocumentMetadata, IngestResponse
from app.services.ingestion import (
    extract_text_from_file,
    chunk_text_fixed_size,
    chunk_text_by_paragraph,
)
from app.services.vector_store import store_chunks_in_qdrant
from app.models import ChatRequest, ChatResponse
from app.services.llm import generate_rag_response
from app.models import InterviewBooking

# Create SQLite tables automatically
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Conversational RAG API",
    description="Palm Mind Internship Technical Assessment Service",
    version="1.0.0",
)


@app.get("/")
def health_check():
    return {"status": "online", "message": "Conversational RAG Backend is running"}


@app.post("/ingest", response_model=IngestResponse, tags=["Document Ingestion"])
async def ingest_document(
    file: UploadFile = File(...),
    strategy: str = Form("fixed", description="Chunking strategy: 'fixed' or 'paragraph'"),
    db: Session = Depends(get_db),
):
    """Upload PDF/TXT, apply selectable chunking, store embeddings in Qdrant, and save metadata."""
    if not file.filename.lower().endswith((".pdf", ".txt")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file format. Only .pdf and .txt files are accepted.",
        )

    try:
        file_bytes = await file.read()
        raw_text = extract_text_from_file(file_bytes, file.filename)

        if strategy == "fixed":
            chunks = chunk_text_fixed_size(raw_text)
        elif strategy == "paragraph":
            chunks = chunk_text_by_paragraph(raw_text)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid strategy. Choose 'fixed' or 'paragraph'.",
            )

        stored_count = store_chunks_in_qdrant(chunks, file.filename)

        # Save metadata to SQLite
        metadata = DocumentMetadata(
            filename=file.filename,
            strategy=strategy,
            chunk_count=stored_count,
        )
        db.add(metadata)
        db.commit()

        return IngestResponse(
            message="Document processed and indexed successfully.",
            filename=file.filename,
            strategy_used=strategy,
            chunks_stored=stored_count,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )

@app.post("/chat", response_model=ChatResponse, tags=["Conversational RAG"])
def chat(request: ChatRequest, db: Session = Depends(get_db)):
    """Conversational endpoint supporting RAG retrieval, history tracking, and booking extraction."""
    try:
        res = generate_rag_response(
            session_id=request.session_id,
            query=request.query,
            db=db,
        )
        return ChatResponse(
            session_id=res["session_id"],
            response=res["response"],
            booking_detected=res["booking_detected"],
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@app.get("/bookings", tags=["Bookings"])
def get_all_bookings(db: Session = Depends(get_db)):
    """Retrieve all extracted interview bookings stored in SQLite."""
    bookings = db.query(InterviewBooking).all()
    return {"count": len(bookings), "bookings": bookings}