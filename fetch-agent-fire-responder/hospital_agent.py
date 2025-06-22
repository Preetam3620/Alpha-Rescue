from uagents import Agent, Context
# from messages import EmergencyNote, MedicalNeed, HospitalResponse
from supabase import create_client
import os
import json
import re
import ast
import requests
import math
from dotenv import load_dotenv
from google.generativeai import configure, GenerativeModel
from sentence_transformers import SentenceTransformer
from typing import Any, List, Optional
from pydantic import BaseModel

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

class HospitalResponse(BaseModel):
    name: str
    address: str
    type: str = "hospital"
    distance: float
    lat: float
    lon: float
    
load_dotenv()

# Environment variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Initialize clients
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
configure(api_key=GEMINI_API_KEY)

# Initialize models
model = GenerativeModel(
    model_name="models/gemini-2.5-flash",
    generation_config={"temperature": 0.3}
)
embedder = SentenceTransformer("all-MiniLM-L6-v2")

# Create the combined agent
hospital_agent = Agent(name="hospital_agent", seed="emergency_secret", port=8000)
hospital_agent_ADDRESS = hospital_agent.address
print(f"[hospital_agent] hospital_agent_ADDRESS: {hospital_agent_ADDRESS}")

# Classification functions (from rag_classifier_og.py)
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

def classify_emergency(note: EmergencyNote) -> MedicalNeed:
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

# Hospital selection functions (from selector_agent.py)
def select_best_hospital(need: MedicalNeed) -> HospitalResponse:
    lat, lng = need.latitude, need.longitude
    
    url = (
        f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?"
        f"location={lat},{lng}&radius=15000&type=hospital&key={GOOGLE_MAPS_API_KEY}"
    )
    
    res = requests.get(url)
    data = res.json()
    hospitals = []

    for result in data.get("results", []):
        name = result.get("name")
        address = result.get("vicinity")
        location = result.get("geometry", {}).get("location", {})
        rating = result.get("rating", 3.0)
        lat2 = location.get("lat")
        lng2 = location.get("lng")

        distance = math.sqrt((lat - lat2)**2 + (lng - lng2)**2) * 111

        if distance > 15:
            continue

        hospital = HospitalResponse(
            name=name,
            address=address,
            distance=round(distance, 2),
            lat=lat2,
            lon=lng2,
            type="hospital"
        )

        hospitals.append((rating, -distance, hospital))

    if hospitals:
        # Sort by highest rating, then by closest distance
        best_rating, best_neg_distance, best = sorted(hospitals, key=lambda x: (-x[0], x[1]))[0]
        print(f"[hospital_agent] 🏥 Selected hospital: {best.name} with rating {best_rating}")
        return best
    else:
        print("[hospital_agent] ❌ No hospitals found nearby.")
        return None

# Main message handler
@hospital_agent.on_message(model=EmergencyNote)
async def handle_emergency_note(ctx: Context, sender: str, note: EmergencyNote):
    print(f"[hospital_agent] 🚨 Received EmergencyNote: {note}")
    
    try:
        # Step 1: Classify the emergency
        print(f"[hospital_agent] 🧠 Classifying emergency...")
        medical_need = classify_emergency(note)
        print(f"[hospital_agent] ✅ Classification result: {medical_need.category}")
        
        # Step 2: Select the best hospital
        print(f"[hospital_agent] 🏥 Finding best hospital...")
        hospital_response = select_best_hospital(medical_need)
        
        if hospital_response:
            print(f"[hospital_agent] ✅ Found hospital: {hospital_response.name}")
            await ctx.send(sender, hospital_response)
        else:
            print(f"[hospital_agent] ❌ No suitable hospital found")
            # You might want to send an error response here
            
    except Exception as e:
        print(f"[hospital_agent] ❌ Error processing emergency: {e}")
        # You might want to send an error response here

if __name__ == "__main__":
    hospital_agent.run()