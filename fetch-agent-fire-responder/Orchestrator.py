# orchestrator_agent.py
import os
import json
from typing import Optional
import google.generativeai as genai
import requests
from uagents import Agent, Context, Model
from dotenv import load_dotenv
from pydantic import BaseModel

from address_2_coord import get_smart_coordinates


load_dotenv()

class IncidentReport(BaseModel):
    incident_report: str
    reporter_name: str
    reporter_phone: str
    reporter_address: Optional[str] = None
    type: str  # e.g., 'fire_station' or 'police_station'
    lat: float
    lon: float

class VAPIData(Model):
    name: str
    address: str
    transcript: str

class AmbulanceRequest(BaseModel):
    note: str
    lat: float
    lon: float
    request_id: str

class EmergencyNote(BaseModel):
    note: str
    latitude: float
    longitude: float

# ──────────────────────────── Gemini SDK ────────────────────────────
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
gemini = genai.GenerativeModel(
    model_name="models/gemini-2.5-flash",
    generation_config={"temperature": 0.3}
)

# ──────────────────────────── Message schema ────────────────────────
class ServiceMsg(BaseModel):
    text: str

# ──────────────────────────── uAgent set-up ─────────────────────────
orchestrator_agent = Agent(
    name="orchestrator",
    port=8100,
    seed="orchestrator demo",
    endpoint="http://127.0.0.1:8100/submit",
    mailbox=True,
)

# env vars for downstream agent DIDs
AMBULANCE_DID  = os.getenv("AMBULANCE_DID")      # did:fetch:…
POLICE_DID  = os.getenv("POLICE_DID")
FIRE_DID = os.getenv("FIRE_DID")
HOSPITAL_DID = os.getenv("HOSPITAL_DID")

# ────────────────────────── Vapi web-hook REST in ───────────────────
# @orchestrator_agent.on_message(model=VAPIData, replies=IncidentReport)
@orchestrator_agent.on_rest_post(endpoint="/vapi-callback", request=VAPIData, response=IncidentReport)
async def vapi_webhook(ctx: Context, req: VAPIData):               # raw starlette Request
    # body = await req.json()
    # if body.get("event") != "call.completed":
    #     return {"ok": True}                              # ignore mid-call pings

    # transcript = body["data"]["transcript"]              # full text string
    ctx.logger.info(f"Vapi data received: {req}")
    transcript = req.transcript
    ctx.logger.info("📞 Vapi transcript received")
    vague_place = req.address
    _lat, _lon = get_smart_coordinates(vague_place)
    ctx.logger.info(f"Smart coordinates for '{vague_place}': lat={_lat}, lon={_lon}")
    # --- Build user info payload ---
    user_payload = {
        "type": "user",
        "name": getattr(req, "name", "Unknown"),
        "location": vague_place,
        "phone": "000-000-0000",         # Default phone
        "age": 0,                        # Default age
        "injuryStatus": "unknown",       # Default injury status
        "lat": _lat,
        "lon": _lon,
        "transcript": transcript
    }
    ctx.logger.info(f"User payload: {user_payload}")

    # --- Make POST request to backend URL from env ---
    backend_url = os.getenv("BACKEND_URL")
    headers = {"Content-Type": "application/json"}
    try:
        resp = requests.post(backend_url, json=user_payload, headers=headers, timeout=10)
        resp.raise_for_status()
        ctx.logger.info(f"User info posted successfully. Response: {resp.text}")
    except requests.exceptions.RequestException as e:
        ctx.logger.error(f"Failed to post user info: {e}")

    # ...rest of your existing code...

    # ── 1 ► Gemini summarization
    # --- inside the background worker ---------------------------------
    prompt = (
        "You are an emergency-dispatch analyst. "
        "Read the transcript of an emergency phone call, decide whether each of "
        "the three public-safety services is REQUIRED, and output one JSON object.\n\n"
        "Services and criteria:\n"
        "• Ambulance  - medical emergencies, injuries, unconscious or ill persons, person might be in an accidet and is having major or minor injuries.\n"
        "• Police     - crimes, violence, safety threats, traffic collisions, someone has broken a law or have seen someone else breaking the law, reporting for the disturbacnce caused by sorroundings or people nearby.\n"
        "• Fire       - fires, explosions, gas leaks, hazardous-material spills, people stuck in places, need help in managging the mob, stuck at crowded or lonely place.\n\n"
        "OUTPUT FORMAT (exactly):\n"
        "{\n"
        '  "Ambulance": "<summary or empty string>",\n'
        '  "Police":    "<summary or empty string>",\n'
        '  "Fire":      "<summary or empty string>"\n'
        "}\n\n"
        "Rules:\n"
        "• Every summary must contain all the basic details given in the above text from the victim such as their name, location precise or whatever they have mentioned as this will summary will be passed directly to respective authorities .\n"
        "• If a service is NOT needed, return an empty string for that key.\n"
        "• If a service IS needed, give ONE concise sentence with all the above details "
        "  (name, location, etc.) in the summary.\n"
        "  describing what is required.\n"
        "• Do **not** add extra keys or commentary.\n\n"
        "TRANSCRIPT:\n"
        f"{transcript}"
    )

    response = gemini.generate_content(prompt)
    # print("Gemini response:", response)

    try:
        # The model sometimes wraps the JSON in markdown code fences.
        json_text = response.text.strip()
        if json_text.startswith("```json"):
            json_text = json_text.strip("```json").strip()
        
        service_dict = json.loads(json_text)

    except json.JSONDecodeError as e:
        ctx.logger.error(f"Gemini output not valid JSON: {response.text}")
        ctx.logger.error(f"JSONDecodeError: {e}")
        return {"ok": False, "error": "Invalid Gemini output"}
    except Exception as e:
        ctx.logger.error(f"An unexpected error occurred while parsing JSON: {e}")
        return {"ok": False, "error": "An unexpected error occurred during parsing"}

    ctx.logger.info(f"Service dictionary: {service_dict}")

    print("Service dictionary:", service_dict)
    # Simple logic: check each service and send if there's a value
    if service_dict.get("Ambulance", "").strip():
        request = AmbulanceRequest(
            request_id="test-001",
            note=service_dict["Ambulance"],
            lat=_lat,
            lon=_lon
        )
        await ctx.send(AMBULANCE_DID, request)

        ctx.logger.info(f"Sending incident report to ambulance: {request}")
        # await ctx.send(AMBULANCE_DID, resp)

        ctx.logger.info(f"sent Ambulance → {AMBULANCE_DID}…")

    # if service_dict.get("Ambulance", "").strip():
    #     ctx.logger.info(f"Sending incident report to hospital: {service_dict['Ambulance']}")
    #     request = EmergencyNote(
    #         note=service_dict["Ambulance"],
    #         latitude=_lat,
    #         longitude=_lon
    #     )

    #     ctx.logger.info(f"Sending incident report to hospital: {request}")
    #     await ctx.send(HOSPITAL_DID, request)

    #     ctx.logger.info(f"sent Ambulance → {HOSPITAL_DID}…")
    
    # if service_dict.get("Police", "").strip():
    #     resp = IncidentReport(
    #         incident_report=service_dict["Police"],
    #         reporter_name=getattr(req, "name", "Unknown"),
    #         reporter_phone="6693401813",
    #         type="police_station",
    #         lat=_lat,
    #         lon=_lon
    #     )
    #     ctx.logger.info(f"Sending incident report to police: {resp}")
    #     await ctx.send(POLICE_DID, resp)

    #     ctx.logger.info(f"sent Police → {POLICE_DID}…")
    
    if service_dict.get("Fire", "").strip():
        resp = IncidentReport(
            incident_report=service_dict["Fire"],
            reporter_name=getattr(req, "name", "Unknown"),
            reporter_phone="6693401813",
            type="fire_station",
            lat=_lat,
            lon=_lon
        )
        ctx.logger.info(f"Sending incident report to fire station: {resp}")
        await ctx.send(FIRE_DID, resp)

        ctx.logger.info(f"sent Fire → {FIRE_DID}…")

# ────────────────────────── house-keeping logs ──────────────────────
@orchestrator_agent.on_event("startup")
async def announce(ctx: Context):
    ctx.logger.info(f"🧩 Orchestrator running at DID: {ctx.agent.address}")

if __name__ == "__main__":
    orchestrator_agent.run()
