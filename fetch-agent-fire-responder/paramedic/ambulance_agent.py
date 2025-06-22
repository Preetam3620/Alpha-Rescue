from uagents import Agent, Context
from messages import AmbulanceRequest, AmbulanceDispatchFinalResponse
from dotenv import load_dotenv
from supabase import create_client, Client
from groq_classifier import get_best_facility
import os
import json
import requests

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
BACKEND_URL = os.getenv("BACKEND_URL")

# Connect to Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Inject supabase into classifier before agent starts
get_best_facility.supabase = supabase  # optional if needed statically

# Initialize the agent
ambulance_agent = Agent(
    name="ambulance_agent",
    seed="ambulance_agent_seed",
    port=8003,
    endpoint="http://127.0.0.1:8003/submit",
)

@ambulance_agent.on_message(model=AmbulanceRequest)
async def handle_ambulance_dispatch(ctx: Context, sender: str, msg: AmbulanceRequest):
    ctx.logger.info(f"📍 Received request to dispatch ambulance near: ({msg.lat}, {msg.lon})")
    try:
        # Corrected function call — removed unexpected kwarg
        best_facility, ambulance_type = get_best_facility(msg.note, msg.lat, msg.lon)
        
        response = AmbulanceDispatchFinalResponse(
            type="paramedic",
            name=best_facility["name"],
            address=best_facility["address"],
            distance=best_facility["distance"],
            lat=best_facility["lat"],
            lon=best_facility["lon"],
        )
        print("DEBUG response object:", response)
        
        # Convert response to dictionary for JSON processing
        response_dict = response.model_dump()
        json_string = json.dumps(response_dict, indent=2)
        ctx.logger.info(f"JSON Output: {json_string}")
        ctx.logger.info(f"Response Output: {response_dict}")

        # --- Convert to AgentInfo format (same as police agent) ---
        agent_info = {
            "type": "paramedic",  # hardcoded as requested
            "name": response_dict.get("name", ""),
            "address": response_dict.get("address", ""),
            "distance": str(response_dict.get("distance", "")),
            "contact": "",  # Add contact info if available in your facility data
            "lat": response_dict.get("lat", ""),
            "lon": response_dict.get("lon", "")
        }
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
        
        await ctx.send(sender, response)
        ctx.logger.info(f"✅ Dispatched: {response.name} [{ambulance_type}] ({response.distance} km away)")

    except Exception as e:
        ctx.logger.error(f"❌ Error dispatching ambulance: {e}")

if __name__ == "__main__":
    ambulance_agent.run()