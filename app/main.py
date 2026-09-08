from fastapi import FastAPI
from app.db import Base, engine

# Automatically create database tables if they don't exist
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Conversational RAG API",
    description="Palm Mind Internship Technical Assessment Service",
    version="1.0.0",
)

@app.get("/")
def health_check():
    return {"status": "online", "message": "Conversational RAG Backend is running"}