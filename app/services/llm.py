import json
import time
from typing import Dict, Any, List
from google import genai
from sqlalchemy.orm import Session
from app.config import settings
from app.models import InterviewBooking
from app.services.vector_store import search_relevant_chunks

try:
    import redis
    redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
    redis_client.ping()
    USE_REDIS = True
except Exception:
    USE_REDIS = False
    in_memory_history: Dict[str, List[Dict[str, str]]] = {}


def call_gemini_with_retry(prompt: str, retries: int = 3, delay: int = 2) -> str:
    """Helper function to execute Gemini requests with automatic retry on 503/transient errors."""
    genai_client = genai.Client(api_key=settings.GEMINI_API_KEY)
    
    for attempt in range(retries):
        try:
            response = genai_client.models.generate_content(
                model="gemini-3.6-flash",
                contents=prompt,
            )
            return response.text.strip()
        except Exception as e:
            if attempt == retries - 1:
                raise e
            time.sleep(delay * (attempt + 1))  # Simple exponential backoff
    return ""


def get_chat_history(session_id: str) -> List[Dict[str, str]]:
    if USE_REDIS:
        data = redis_client.get(f"chat:{session_id}")
        return json.loads(data) if data else []
    return in_memory_history.get(session_id, [])


def save_chat_history(session_id: str, history: List[Dict[str, str]]) -> None:
    trimmed = history[-10:]
    if USE_REDIS:
        redis_client.set(f"chat:{session_id}", json.dumps(trimmed), ex=86400)
    else:
        in_memory_history[session_id] = trimmed


def extract_and_save_booking(user_query: str, db: Session) -> bool:
    prompt = f"""
    Analyze the user message. If they are attempting to schedule or book an interview/meeting, 
    extract the information into JSON format with keys: "name", "email", "date", "time".
    If they are not booking an interview, reply strictly with "NONE".

    User Message: "{user_query}"

    JSON format if applicable:
    {{
      "name": "Full Name",
      "email": "email@example.com",
      "date": "YYYY-MM-DD",
      "time": "HH:MM"
    }}
    """
    try:
        text = call_gemini_with_retry(prompt).strip()
        
        if "NONE" in text:
            return False

        # Clean markdown code fences if Gemini wraps the response in ```json ... ```
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
            text = text.strip()

        data = json.loads(text)
        
        # Ensure essential keys are present
        if not data.get("name") and not data.get("email"):
            return False

        booking = InterviewBooking(
            name=data.get("name", "Unknown"),
            email=data.get("email", "Unknown"),
            date=str(data.get("date", "Unspecified")),
            time=str(data.get("time", "Unspecified")),
        )
        db.add(booking)
        db.commit()
        return True
    except Exception as e:
        print(f"[Extraction Error]: {e}")
        return False


def generate_rag_response(session_id: str, query: str, db: Session) -> Dict[str, Any]:
    retrieved_chunks = search_relevant_chunks(query, limit=3)
    context_text = "\n\n".join(retrieved_chunks) if retrieved_chunks else "No specific document context found."

    history = get_chat_history(session_id)
    history_str = "\n".join([f"{msg['role'].upper()}: {msg['content']}" for msg in history])

    prompt = f"""
    You are an intelligent AI assistant. Use the following document context and history to answer the user's question accurately.

    Document Context:
    {context_text}

    Chat History:
    {history_str}

    User Question: {query}
    """

    try:
        answer = call_gemini_with_retry(prompt)
    except Exception:
        answer = "The AI service is currently experiencing high demand. Please try sending your message again in a few moments."

    booking_detected = extract_and_save_booking(query, db)

    history.append({"role": "user", "content": query})
    history.append({"role": "assistant", "content": answer})
    save_chat_history(session_id, history)

    return {
        "session_id": session_id,
        "response": answer,
        "booking_detected": booking_detected,
    }