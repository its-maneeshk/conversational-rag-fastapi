# Conversational RAG & Automated Interview Booking Service

Conversational Retrieval-Augmented Generation (RAG) backend built using FastAPI, Qdrant vector database, Google Gemini API (`gemini-3.6-flash` and `text-embedding-004`), Redis, and SQLite.

The service provides dynamic document ingestion, context-aware conversational search with multi-turn memory, and automated entity extraction to parse interview booking requests directly into a relational database.

---

## 1. System Architecture & Key Features

* **Document Processing & Ingestion (`POST /ingest`):** Supports PDF and plain-text (`.txt`) files. Features selectable chunking strategies ('fixed' character length vs. 'paragraph'-based splitting) and converts text chunks into 768-dimensional vector embeddings using Google's `text-embedding-004`.
* **Vector Indexing & Retrieval:** Stores chunk embeddings and payloads in a local or cloud Qdrant collection using Cosine similarity.
* **Conversational RAG (`POST /chat`):** Embeds incoming queries, retrieves top-K matching chunks from Qdrant, and synthesizes answers using `gemini-3.6-flash`.
* **Stateful Chat Memory:** Persists up to 10 context turns per `session_id` using Redis (with an automatic in-memory dictionary fallback).
* **Automated Interview Extraction:** Analyzes user input during conversation for interview scheduling intent. Extracts parameters (name, email, date, time) and saves valid records directly into SQLite.
* **Resilience & Fault Tolerance:** Implements exponential backoff retry logic for transient API/LLM errors (HTTP 503) and sanitizes markdown-wrapped JSON responses from the LLM.

---

## 2. Technology Stack

* **Framework:** Python 3.10+ / FastAPI
* **LLM & Embeddings:** Google genai SDK (`gemini-3.6-flash`, `text-embedding-004`)
* **Vector Database:** Qdrant (`qdrant-client`)
* **Caching & Session Memory:** Redis
* **Relational Database:** SQLite (managed via SQLAlchemy ORM)
* **ASGI Server:** Uvicorn

---

## 3. Project Structure

```text
conversational-rag-fastapi/
├── app/
│   ├── __init__.py
│   ├── main.py              # Application entry point & API routes
│   ├── config.py            # Environment variable loading & validation
│   ├── database.py          # SQLAlchemy session and engine initialization
│   ├── models.py            # Pydantic schemas & SQLAlchemy DB models
│   └── services/
│       ├── __init__.py
│       ├── ingestion.py     # PDF/TXT parsing and chunking logic
│       ├── vector_store.py  # Qdrant client interactions & embeddings
│       └── llm.py           # Gemini RAG generation, Redis memory & extraction
├── .env.example             # Template for required environment variables
├── .gitignore
├── requirements.txt         # Project dependencies
└── README.md                # System documentation
```

---

## 4. Environment Variables Configuration

Create a `.env` file in the root directory based on `.env.example`:

```bash
GEMINI_API_KEY="your_google_gemini_api_key"
QDRANT_URL="http://localhost:6333"
QDRANT_API_KEY="visit https://qdrant.tech/documentation/cloud-api/ to create api key"
REDIS_URL="redis://localhost:6379/0"
DATABASE_URL="sqlite:///./app.db"
```

---

## 5. Local Setup & Installation

### Step 1: Clone the Repository
```bash
git clone https://github.com/its-maneeshk/conversational-rag-fastapi.git
cd conversational-rag-fastapi
```

### Step 2: Create and Activate a Virtual Environment
* **Windows (PowerShell):**
  ```powershell
  python -m venv .venv  <- to create isolated virtual environment
  .\.venv\Scripts\activate <- to actiavte that isolated virtual environment
  ```
* **Linux / macOS:**
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  ```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt  <- to install all required dependencies by this project.
```

---

## 6. Running the Application

Start the FastAPI development server using Uvicorn:

```bash
unicorn app.main:app --reload
            [or]
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Access API docs at:
* **Swagger UI:** http://127.0.0.1:8000/docs
* **ReDoc:** http://127.0.0.1:8000/redoc

---

## 7. API Reference & Endpoint Usage

### 7.1 Health Check
* **Route:** `GET /`
* **Description:** Verifies server runtime status.

### 7.2 Document Ingestion
* **Route:** `POST /ingest`
* **Content Type:** `multipart/form-data`
* **Parameters:** `file` (UploadFile, required), `strategy` ('fixed' or 'paragraph')

### 7.3 Conversational RAG & Booking Chat
* **Route:** `POST /chat`
* **Content Type:** `application/json`
* **Parameters:** `session_id` (string), `query` (string)
* **Description:** Conversation about document ingested and Booking slot on prefered time & date.

### 7.4 Inspect Bookings
* **Route:** `GET /bookings`
* **Description:** Retrieves all interview booking records extracted from conversations and stored in SQLite.
