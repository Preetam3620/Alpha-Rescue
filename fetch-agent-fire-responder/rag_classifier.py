# rag_classifier.py

import json
import os
import re
import ast
from typing import List, Optional
from dotenv import load_dotenv
from pydantic import BaseModel
from supabase import create_client
from google.generativeai import configure, GenerativeModel
from sentence_transformers import SentenceTransformer

class EmergencyNote(BaseModel):
    note: str
    latitude: float
    longitude: float

class MedicalNeed(BaseModel):
    category: List[str]
    latitude: float
    longitude: float
    context: Optional[str] = None
    prompt: Optional[str] = None
    raw_response: Optional[str] = None

# Load environment variables
load_dotenv()

# Supabase setup
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Gemini setup for generation
configure(api_key=os.getenv("GEMINI_API_KEY"))

model = GenerativeModel(
    model_name="models/gemini-2.5-flash",
    generation_config={"temperature": 0.3}
)

# Local embedding model
embedder = SentenceTransformer("all-MiniLM-L6-v2")

def get_embedding(text):
    return embedder.encode(text).tolist()

def search_supabase(query: str, top_k=3):
    embed = get_embedding(query)
    embed_str = ",".join(map(str, embed))

    sql = f"""
    select id, content, metadata,
    1 - (embedding <=> '[{embed_str}]') as similarity
    from medical_docs
    order by embedding <=> '[{embed_str}]'
    limit {top_k}
    """

    response = supabase.rpc("execute_sql_from_json", {"input": {"sql": sql}}).execute()
    return response.data

def format_prompt(context_docs, note):
    context = "\n\n".join([doc["content"] for doc in context_docs])
    return f"""
You are a medical classification assistant helping 911 dispatchers.

Context:
{context}

Paramedic Note:
{note}

Classify the post-first-aid medical needs of the patient. Return the result as a Python list like this:
["burn", "trauma", "ICU"]
"""

def safe_parse_gemini_list(output):
    try:
        match = re.search(r"\[(.*?)\]", output, re.DOTALL)
        if match:
            raw_items = match.group(1)
            items = [item.strip().strip("\"'") for item in raw_items.split(",")]
            return [i for i in items if i]
        return ast.literal_eval(output)
    except Exception:
        return []

def classify_emergency(note: EmergencyNote, supabase) -> MedicalNeed:
    docs = search_supabase(note.note, top_k=5)
    prompt = format_prompt(docs, note.note)
    response = model.generate_content(prompt)

    parsed_needs = safe_parse_gemini_list(response.text.strip())

    return MedicalNeed(
        category=parsed_needs,
        latitude=note.latitude,
        longitude=note.longitude,
        context=json.dumps(docs),
        prompt=prompt,
        raw_response=response.text.strip()
    )
