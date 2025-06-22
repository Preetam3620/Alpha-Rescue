import os
import requests
import json
import math
from uagents import Agent, Context, Model
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

# --- Configuration: set your Google API key in the environment ---
# GOOGLE_API_KEY = "AIzaSyC0WVoj1w-ev9tDosmdRkidxSbLQhMeIKo"
# GOOGLE_API_KEY = "AIzaSyA1ye2eGiHQYd9kYZFRZsJLeNgKE3zj7Tc"
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# --- VAPI Configuration ---
# IMPORTANT: Replace these placeholders with your actual credentials.
# VAPI_AUTH_TOKEN = "d1fa0d9f-a590-46c6-9c7a-11930c2475bb"  # Found in VAPI Dashboard -> Develop -> API Keys
# VAPI_ASSISTANT_ID = "7f061471-d28e-49d1-b17c-ac39976b2690" # The ID of the assistant you created in VAPI
# RECIPIENT_PHONE_NUMBER = "+16693406332"  # The full phone number to call, including country code
# PHONE_NUMBER_ID = "35f01740-9318-44ee-8eb1-c500f6878a8c"
VAPI_AUTH_TOKEN = os.getenv("VAPI_AUTH_TOKEN")
VAPI_ASSISTANT_ID = os.getenv("VAPI_ASSISTANT_ID")
RECIPIENT_PHONE_NUMBER = os.getenv("RECIPIENT_PHONE_NUMBER")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")

# --- Request/Response Schemas ---
class IncidentReport(BaseModel):
    incident_report: str
    reporter_name: str
    reporter_phone: str
    reporter_address: Optional[str] = None
    type: str  # e.g., 'fire_station' or 'police_station'
    lat: float
    lon: float

class Facility(BaseModel):
    name: str
    address: str
    latitude: float
    longitude: float
    distance_miles: str

class DispatchedIncidentReport(IncidentReport):
    facility: Optional[Facility] = None

def get_address_from_coords(lat: float, lon: float, api_key: str, ctx: Context) -> str | None:
    """
    Performs reverse geocoding to get a human-readable address from coordinates.

    Args:
        lat: The latitude.
        lon: The longitude.
        api_key: Your Google Cloud Platform API key.

    Returns:
        A formatted address string, or None if an address could not be found.
    """
    if not api_key or "your-api-key" in api_key:
        print("ERROR: Google API key is not configured.")
        return None

    # Construct the API request URL
    url = (
        "https://maps.googleapis.com/maps/api/geocode/json"
        f"?latlng={lat},{lon}&key={api_key}"
    )
    ctx.logger.info(f"URL: {url}")
    try:
        # Make the API call
        response = requests.get(url, timeout=5)
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
        data = response.json()
        # ctx.logger.info(f"Data: {data}")
        # Check the API response status and ensure results exist
        if data["status"] == "OK" and data["results"]:
            # The first result is typically the most specific and accurate one
            address = data["results"][0]["formatted_address"]
            ctx.logger.info(f"Address: {address}")
            return address
        else:
            # Handle cases like coordinates in the middle of the ocean
            print(f"Warning: Could not find address for lat/lon. Status: {data['status']}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"Error during reverse geocoding API call: {e}")
        return None

def create_spoken_summary(msg: DispatchedIncidentReport) -> str:
    """Creates a direct, professional dispatch summary for a phone call."""
    
    # Using a list to build the message cleanly
    summary_parts = [
        "This is a critical dispatch alert.",
        f"An incident has been reported at the address {msg.reporter_address}.",
        f"It is reported by {msg.reporter_name}.",
        f"Reporter's contact phone is {msg.reporter_phone}.",
        "The incident is:",
        f"{msg.incident_report}.",
        f"Requesting {msg.type.replace('_', ' ')} support."
    ]

    # Add details about the dispatched unit, if one was found
    if msg.facility:
        facility = msg.facility

    else:
        summary_parts.append(
            f"No nearby {msg.type.replace('_', ' ')} could be automatically located. This incident requires manual review."
        )
    
    # Join all the parts into a single string for VAPI to speak
    return " ".join(summary_parts)

# --- Helper Function to Make the VAPI Call ---
def make_vapi_call(phone_number: str, message: str, ctx: Context):
    """Initiates a fire-and-forget phone call using the VAPI API."""
    ctx.logger.info(f"Initiating call to {phone_number} via VAPI...")
    
    url = "https://api.vapi.ai/call"
    headers = {
        "Authorization": f"Bearer {VAPI_AUTH_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "type": "outboundPhoneCall",
        "phoneNumberId": PHONE_NUMBER_ID,
        "customer": {
            "number": phone_number
        },
        "assistant": {
            "firstMessage": message,
        }
    }

    try:
        ctx.logger.info(f"Making VAPI call to {url} with headers: {headers} and payload: {payload}")
        # response = requests.post("url", headers=headers, json=payload, timeout=10)
        # response.raise_for_status()  # This will raise an exception for HTTP errors (4xx or 5xx)
        # ctx.logger.info(f"VAPI call initiated successfully. Response: {response.json()}")
    except requests.exceptions.RequestException as e:
        ctx.logger.error(f"Failed to initiate VAPI call: {e}")

# --- Agent Implementation ---
firestation_lookup_agent = Agent(
    name="firestation_lookup_agent",
    seed="firestation_lookup_agent_seed",
    port=8000,
    endpoint="http://127.0.0.1:8000/submit",
)

# --- Utility: Haversine distance ---
def haversine(lat1, lon1, lat2, lon2):
    R = 3958.8  # Earth radius in miles
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

@firestation_lookup_agent.on_event("startup")
async def on_startup(ctx: Context):
    ctx.logger.info(f"Agent address: {firestation_lookup_agent.address}")

@firestation_lookup_agent.on_message(model=IncidentReport, replies=DispatchedIncidentReport)
async def handle_request(ctx: Context, sender: str, msg: IncidentReport):
    ctx.logger.info(f"Received incident report from {sender} for nearest '{msg.type}'")

    lat, lon = msg.lat, msg.lon
    url = (
        "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
        f"?location={lat},{lon}&radius=5000&type={msg.type}&key={GOOGLE_API_KEY}"
    )
    ctx.logger.info(f"Google Places API URL: {url}")
    try:
        resp = requests.get(url, timeout=5)
        resp.raise_for_status() 
        data = resp.json()
    except Exception as ex:
        ctx.logger.error(f"Error calling Google Places API: {ex}")
        await ctx.send(sender, DispatchedIncidentReport(**msg.model_dump(), facility=None))
        return

    # UPDATED: Process only the single closest facility
    results = data.get("results", [])
    closest_facility = None

    if results:
        # The first result from Google's nearbysearch is the closest by default
        place = results[0]
        name = place.get("name")
        address = place.get("vicinity")
        plat = place["geometry"]["location"]["lat"]
        plon = place["geometry"]["location"]["lng"]
        distance_in_miles = haversine(lat, lon, plat, plon)
        distance_formatted = f"{distance_in_miles:.2f} miles"
        closest_facility = Facility(
            name=name, address=address,
            latitude=plat, longitude=plon,
            distance_miles=distance_formatted
        )
        ctx.logger.info(f"Found closest facility: {name}")
    else:
        ctx.logger.info(f"No facilities of type '{msg.type}' found nearby.")

    # Get the address from the coordinates
    address = get_address_from_coords(lat, lon, GOOGLE_API_KEY, ctx)
    msg.reporter_address = address
    ctx.logger.info(f"Address: {address}")

    # Create the response with the single facility (or None if not found)
    response = DispatchedIncidentReport(**msg.model_dump(), facility=closest_facility)

    response_dict = response.model_dump()
    json_string = json.dumps(response_dict, indent=2)
    ctx.logger.info(f"JSON Output: {response_dict}")
    ##### call api to frontend #####
    facility = response_dict.get("facility", {})
    agent_info = {
    "type": "fire",  # hardcoded as requested
    "name": facility.get("name", ""),
    "address": facility.get("address", ""),
    "distance": str(facility.get("distance_miles", "")),
    "contact": response_dict.get("reporter_phone", ""),
    "lat": facility.get("latitude", ""),
    "lon": facility.get("longitude", "")
    }
    agent_info_json = json.dumps(agent_info, indent=2)
    ctx.logger.info(f"AgentInfo JSON: {agent_info_json}")

    # ...existing code...
    BACKEND_URL = os.getenv("BACKEND_URL")
    # ...existing code...
    # ...existing code...
    agent_info_json = json.dumps(agent_info, indent=2)
    ctx.logger.info(f"AgentInfo JSON: {agent_info_json}")

    # --- POST to your backend ---
    headers = {"Content-Type": "application/json"}
    try:
        resp = requests.post(BACKEND_URL, data=agent_info_json, headers=headers, timeout=10)
        resp.raise_for_status()
        ctx.logger.info(f"Successfully posted to backend. Response: {resp.text}")
    except requests.exceptions.RequestException as e:
        ctx.logger.error(f"Failed to post to backend: {e}")
    # ...existing code...
    #------------
    # Create the spoken summary
    spoken_summary = create_spoken_summary(DispatchedIncidentReport(**msg.model_dump(), facility=closest_facility))
    ctx.logger.info(f"Spoken summary: {spoken_summary}")

    # Make the VAPI call
    make_vapi_call(RECIPIENT_PHONE_NUMBER, spoken_summary, ctx)


    
    ctx.logger.info(f"Sending response: {response}")
    # await ctx.send(sender, response)
    
    if closest_facility:
        ctx.logger.info(f"Replied with the single closest facility.")
    else:
        ctx.logger.info(f"Replied that no facility was found.")
    
    await ctx.send(sender, response)

# --- Entry Point ---
if __name__ == "__main__":
    firestation_lookup_agent.run()
