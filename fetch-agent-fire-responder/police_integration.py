# ... imports & load_dotenv stay the same ...

import json
import math
import os, googlemaps
from typing import Optional
import google.generativeai as genai          # optional Gemini use
from uagents import Agent, Context, Model
from datetime import datetime
from dotenv import load_dotenv
from pydantic import BaseModel
import requests

load_dotenv()                               

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
VAPI_AUTH_TOKEN = os.getenv("VAPI_AUTH_TOKEN")
VAPI_ASSISTANT_ID = os.getenv("VAPI_ASSISTANT_ID")
RECIPIENT_PHONE_NUMBER = os.getenv("RECIPIENT_PHONE_NUMBER")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
gmaps = googlemaps.Client(key=os.getenv("GOOGLE_API_KEY"))      # Places API

class IncidentReport(BaseModel):
    incident_report: str
    reporter_name: str
    reporter_phone: str
    reporter_address: Optional[str] = None
    type: str  # e.g., 'fire_station' or 'police_station'
    lat: float
    lon: float

class ManualIncidentReport(Model):
    incident_report: str
    reporter_name: str
    reporter_phone: str
    reporter_address: Optional[str] = None
    type: str  # e.g., 'fire_station' or 'police_station'
    lat: float
    lon: float

class DispatchStatus(BaseModel):
    ok: bool
    detail: str

class StationInfo(BaseModel):
    name: str
    phone: str
    lat: float
    lon: float

class DispatchedIncidentReport(IncidentReport):
    station: Optional[StationInfo] = None

def nearest_station(lat: float, lon: float):
    results = gmaps.places_nearby(
        location=(lat, lon), radius=5000, type="police"
    )["results"]
    print(f"Found {len(results)} police stations near ({lat}, {lon})")
    if not results:
        return None
    place = gmaps.place(
        place_id=results[0]["place_id"],
        fields=["name", "formatted_phone_number", "geometry"]
    )["result"]
    print(f"Nearest station: {place['name']} at {place['geometry']['location']} and phone {place.get('formatted_phone_number', 'N/A')}")
    return place                            # dict with name/phone/geometry

def haversine(lat1, lon1, lat2, lon2):
    """
    Calculate the great-circle distance between two points on the Earth (in miles).
    """
    # Validate inputs
    if any(coord is None for coord in [lat1, lon1, lat2, lon2]):
        return None
    
    if any(coord == 0 for coord in [lat1, lon1, lat2, lon2]):
        return None
    
    R = 3958.8  # Radius of Earth in miles
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    
    # Clamp 'a' to prevent domain error
    a = max(0, min(1, a))
    
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

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
    if msg.station:
        station = msg.station

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
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()  # This will raise an exception for HTTP errors (4xx or 5xx)
        ctx.logger.info(f"VAPI call initiated successfully. Response: {response.json()}")
    except requests.exceptions.RequestException as e:
        ctx.logger.error(f"Failed to initiate VAPI call: {e}")


police_agent = Agent(
    name="police_caller", 
    port=8001,
    seed="police caller demo", 
    endpoint="http://127.0.0.1:8001/submit",
    # mailbox=True
)

@police_agent.on_event("startup")          # fires once when the agent starts
async def demo_incident(ctx: Context):
    """
    Local self-test: post a fake incident to this very agent.
    Remove or guard with an env-flag once you're done debugging.
    """
    # test_report = IncidentReport(
    #     latitude = 37.7749,                # San Francisco
    #     longitude = -122.4194,
    #     text = "A gas leak near downtown San Jose prompted road closures and emergency response, but no injuries were reported."
    # )
    # send to *our own* DID – ctx.address is the agent's own address
    ctx.logger.info(f"Agent address: {police_agent.address}")
    # await ctx.send(ctx.agent.address, test_report)
    ctx.logger.info("🔄  Self-test IncidentReport queued")

@police_agent.on_message(model=IncidentReport, replies=DispatchedIncidentReport)
async def handle_incident(ctx: Context, sender: str, msg: IncidentReport):
    station = nearest_station(msg.lat, msg.lon)
    ctx.logger.info(f"Station: {station}")
    # await forward_station(ctx, station) 
    if not station or "formatted_phone_number" not in station:
        await ctx.send(sender, DispatchStatus(ok=False, detail="No station found"))
        return
    if station:
        # --- FIX: Manually create a StationInfo object ---
        station_info_obj = StationInfo(
            name=station.get("name"),
            phone=station.get("formatted_phone_number", "N/A"),
            lat=station.get("geometry", {}).get("location", {}).get("lat"),
            lon=station.get("geometry", {}).get("location", {}).get("lng")
        )
    # Get the address from the coordinates
    address = get_address_from_coords(msg.lat, msg.lon, GOOGLE_API_KEY, ctx)
    msg.reporter_address = address
    ctx.logger.info(f"Address: {address}")

    # Create the spoken summary
    # spoken_summary = create_spoken_summary(DispatchedIncidentReport(**msg.model_dump(), station=station))
    # ctx.logger.info(f"Spoken summary: {spoken_summary}")

    # # Make the VAPI call
    # make_vapi_call(RECIPIENT_PHONE_NUMBER, spoken_summary, ctx)

    # # Create the response with the single facility (or None if not found)
    # response = DispatchedIncidentReport(**msg.model_dump(), station=station)
    # ctx.logger.info(f"Response from police_agent: {response}")
    
    # Create the response with the single facility (or None if not found)
    response = DispatchedIncidentReport(**msg.model_dump(), station=station_info_obj)

    response_dict = response.model_dump()
    station = response_dict.get("station", {})
    distance = ""
    if station.get("lat") and station.get("lon") and response_dict.get("lat") and response_dict.get("lon"):
        try:
            distance = haversine(
                response_dict.get("lat"),
                response_dict.get("lon"),
                station.get("lat"),
                station.get("lon")
            )
            if distance is not None:
                distance = f"{distance:.2f} miles"
            else:
                distance = "Unknown"
        except Exception as e:
            ctx.logger.error(f"Error calculating distance: {e}")
            distance = "Error"
    else:
        distance = "No coordinates available"

    json_string = json.dumps(response_dict, indent=2)
    ctx.logger.info(f"JSON Output: {json_string}")
    ctx.logger.info(f"Response Output: {response_dict}")

    # --- Convert to AgentInfo format ---
    station = response_dict.get("station", {})
    agent_info = {
    "type": "police",  # hardcoded as requested
    "name": station.get("name", ""),
    "address": response_dict.get("reporter_address", ""),
    "distance":  str(distance),  # No distance available in your example
    "contact": station.get("phone", response_dict.get("reporter_phone", "")),
    "lat": station.get("lat", ""),
    "lon": station.get("lon", "")
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


    # number  = station["formatted_phone_number"]
    # number = "+16693406255"  # hardcoded for demo purposes
    # summary = f"Emergency reported: {msg.text}"
    # summary = f"Emergency reported: A gas leak near downtown San Jose prompted road closures and emergency response, but no injuries were reported."

    await ctx.send(sender, response)

@police_agent.on_rest_post(endpoint="/manual-trigger-police", request=ManualIncidentReport, response=DispatchedIncidentReport)
async def handle_incident(ctx: Context, sender: str, msg: ManualIncidentReport):
    station = nearest_station(msg.lat, msg.lon)
    ctx.logger.info(f"Station: {station}")
    # await forward_station(ctx, station) 
    if not station or "formatted_phone_number" not in station:
        await ctx.send(sender, DispatchStatus(ok=False, detail="No station found"))
        return
    if station:
        # --- FIX: Manually create a StationInfo object ---
        station_info_obj = StationInfo(
            name=station.get("name"),
            phone=station.get("formatted_phone_number", "N/A"),
            lat=station.get("geometry", {}).get("location", {}).get("lat"),
            lon=station.get("geometry", {}).get("location", {}).get("lng")
        )
    # Get the address from the coordinates
    address = get_address_from_coords(msg.lat, msg.lon, GOOGLE_API_KEY, ctx)
    msg.reporter_address = address
    ctx.logger.info(f"Address: {address}")

    # Create the spoken summary
    # spoken_summary = create_spoken_summary(DispatchedIncidentReport(**msg.model_dump(), station=station))
    # ctx.logger.info(f"Spoken summary: {spoken_summary}")

    # # Make the VAPI call
    # make_vapi_call(RECIPIENT_PHONE_NUMBER, spoken_summary, ctx)

    # # Create the response with the single facility (or None if not found)
    # response = DispatchedIncidentReport(**msg.model_dump(), station=station)
    # ctx.logger.info(f"Response from police_agent: {response}")
    
    # Create the response with the single facility (or None if not found)
    response = DispatchedIncidentReport(**msg.model_dump(), station=station_info_obj)

    response_dict = response.model_dump()
    station = response_dict.get("station", {})
    distance = ""
    if station.get("lat") and station.get("lon") and response_dict.get("lat") and response_dict.get("lon"):
        try:
            distance = haversine(
                response_dict.get("lat"),
                response_dict.get("lon"),
                station.get("lat"),
                station.get("lon")
            )
            if distance is not None:
                distance = f"{distance:.2f} miles"
            else:
                distance = "Unknown"
        except Exception as e:
            ctx.logger.error(f"Error calculating distance: {e}")
            distance = "Error"
    else:
        distance = "No coordinates available"

    json_string = json.dumps(response_dict, indent=2)
    ctx.logger.info(f"JSON Output: {json_string}")
    ctx.logger.info(f"Response Output: {response_dict}")

    # --- Convert to AgentInfo format ---
    station = response_dict.get("station", {})
    agent_info = {
    "type": "police",  # hardcoded as requested
    "name": station.get("name", ""),
    "address": response_dict.get("reporter_address", ""),
    "distance":  str(distance),  # No distance available in your example
    "contact": station.get("phone", response_dict.get("reporter_phone", "")),
    "lat": station.get("lat", ""),
    "lon": station.get("lon", "")
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


    # number  = station["formatted_phone_number"]
    # number = "+16693406255"  # hardcoded for demo purposes
    # summary = f"Emergency reported: {msg.text}"
    # summary = f"Emergency reported: A gas leak near downtown San Jose prompted road closures and emergency response, but no injuries were reported."

    await ctx.send(sender, response)


if __name__ == "__main__":
    police_agent.run()



