import uuid
from typing import List
from google import genai
from google.genai import types
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from app.config import settings

# Initialize Clients
qdrant = QdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY)
genai_client = genai.Client(api_key=settings.GEMINI_API_KEY)

COLLECTION_NAME = "palmmind_documents"
EMBEDDING_MODEL = "gemini-embedding-001"
VECTOR_SIZE = 768


def ensure_collection_exists() -> None:
    """Check if Qdrant collection exists; create if missing."""
    collections = [c.name for c in qdrant.get_collections().collections]
    if COLLECTION_NAME not in collections:
        qdrant.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
        )


def generate_embeddings(texts: List[str]) -> List[List[float]]:
    """Generate 768-dimensional vector embeddings using Gemini API."""
    if not texts:
        return []

    response = genai_client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=texts,
        config=types.EmbedContentConfig(output_dimensionality=VECTOR_SIZE),
    )

    embeddings: List[List[float]] = []
    if hasattr(response, "embeddings") and response.embeddings:
        for emb in response.embeddings:
            embeddings.append(emb.values)
    elif hasattr(response, "embedding") and response.embedding:
        embeddings.append(response.embedding.values)

    return embeddings


def store_chunks_in_qdrant(chunks: List[str], filename: str) -> int:
    """Embed text chunks and upsert into Qdrant collection."""
    if not chunks:
        return 0

    ensure_collection_exists()
    embeddings = generate_embeddings(chunks)
    points: List[PointStruct] = []

    for chunk, vector in zip(chunks, embeddings):
        points.append(
            PointStruct(
                id=str(uuid.uuid4()),
                vector=vector,
                payload={"text": chunk, "filename": filename},
            )
        )

    qdrant.upsert(collection_name=COLLECTION_NAME, points=points)
    return len(points)


def search_relevant_chunks(query: str, limit: int = 3) -> List[str]:
    """Search Qdrant for top-K matching text chunks for a given query."""
    ensure_collection_exists()
    query_vectors = generate_embeddings([query])
    if not query_vectors:
        return []

    # Use query_points for modern qdrant-client versions
    if hasattr(qdrant, "query_points"):
        search_results = qdrant.query_points(
            collection_name=COLLECTION_NAME,
            query=query_vectors[0],
            limit=limit,
        ).points
    else:
        search_results = qdrant.search(
            collection_name=COLLECTION_NAME,
            query_vector=query_vectors[0],
            limit=limit,
        )

    return [
        hit.payload["text"]
        for hit in search_results
        if hit.payload and "text" in hit.payload
    ]