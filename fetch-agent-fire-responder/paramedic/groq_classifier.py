from geopy.distance import geodesic
from supabase import create_client
import os
import groq
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
GROQ_MODEL ="llama3-70b-8192"

supabase = create_client(SUPABASE_URL, "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhuZHJteHF0bHdweHNmanZuaWpmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTA0MDAxMjksImV4cCI6MjA2NTk3NjEyOX0.zNAVC_PrJZ7OimbNzgoQ6LuOxkQTqWA_cQvcwhRhVHQ")
groq_client = groq.Client(api_key=GROQ_API_KEY)

def classify_ambulance_type(note: str) -> str:
    prompt = (
        "Classify this emergency as one of the following ambulance types:\n"
        "- BLS: Basic Life Support (minor injuries, stable condition)\n"
        "- ALS: Advanced Life Support (unconscious, respiratory or cardiac issues)\n"
        "- CCT: Critical Care Transport (ICU transfer, ventilator, critical condition)\n\n"
        f"Incident report:\n{note}\n\n"
        "Reply with only one of: BLS, ALS, or CCT."
    )

    try:
        response = groq_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": "You are a trained emergency medical classifier."},
                {"role": "user", "content": prompt}
            ]
        )
        classification = response.choices[0].message.content.strip().upper()
        print("🔍 Classified ambulance type:", classification)
        return classification
    except Exception as e:
        print(f"❌ Groq classification error: {e}")
        raise

def get_best_facility(note: str, lat: float, lon: float):
    ambulance_type = classify_ambulance_type(note)

    try:
        response = supabase.table("facilities") \
            .select("*") \
            .eq("type", "paramedic") \
            .eq("ambulance_type", ambulance_type) \
            .execute()
        facilities = response.data
    except Exception as e:
        print(f"❌ Supabase query failed: {e}")
        raise

    if not facilities:
        print(f"⚠️ No facilities found for ambulance type: {ambulance_type}")
        return None, ambulance_type

    best = None
    min_dist = float("inf")

    for facility in facilities:
        dist_km = geodesic((lat, lon), (facility["lat"], facility["lon"])).km
        # Convert kilometers to miles (1 km = 0.621371 miles)
        dist_miles = dist_km * 0.621371
        
        if dist_miles < min_dist:
            min_dist = dist_miles
            best = {
                "name": facility["name"],
                "address": facility["address"],
                "lat": float(facility["lat"]),
                "lon": float(facility["lon"]),
                "distance": f"{dist_miles:.2f} miles",
                "ambulance_type": ambulance_type
            }
    if not facilities:
        print(f"⚠️ No facilities found for ambulance type: {ambulance_type}")
        return None, ambulance_type
    print("✅ Best facility selected:", best)
    return best, ambulance_type
