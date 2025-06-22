import requests
from uagents import Agent, Context
from pydantic import BaseModel
from typing import Optional

# Import the shared models
class IncidentReport(BaseModel):
    incident_report: str
    reporter_name: str
    type: str
    lat: float
    lon: float

class Facility(BaseModel):
    name: str
    address: str
    latitude: float
    longitude: float
    distance_miles: float

class DispatchedIncidentReport(IncidentReport):
    facility: Optional[Facility] = None

class NotificationStatus(BaseModel):
    success: bool
    message: str

# --- VAPI Configuration ---
VAPI_AUTH_TOKEN = "47653ae2-42f9-43fe-bbfe-8c59c3989400"  # Found in VAPI Dashboard -> Develop -> API Keys
VAPI_ASSISTANT_ID = "c55d6669-a5ce-48f3-bbbf-b3584e890de2" # The ID of the assistant you created in VAPI
RECIPIENT_PHONE_NUMBER = "+16693406332"  # The full phone number to call

# --- Agent Implementation ---
vapi_agent = Agent(
    name="vapi_notifier_agent",
    seed="vapi_notifier_agent_seed",
    port=8002,  # Use a new port
    endpoint=["http://127.0.0.1:8002/submit"],
)

@vapi_agent.on_event("startup")
async def on_startup(ctx: Context):
    ctx.logger.info(f"VAPI Notifier Agent started. Address: {vapi_agent.address}")
    if "your-vapi-auth-token" in VAPI_AUTH_TOKEN:
        ctx.logger.warning("VAPI credentials are not set. Phone calls will be skipped.")

# --- Helper Functions for VAPI Logic ---
def create_spoken_summary(msg: DispatchedIncidentReport) -> str:
    """Creates a clear, spoken summary from the incident report."""
    opening = f"Hello. This is an automated dispatch alert regarding an incident reported by {msg.reporter_name}."
    incident = f"The report states: {msg.incident_report}."
    
    if msg.facility:
        facility = msg.facility
        dispatch_info = (
            f"The nearest {msg.type.replace('_', ' ')} has been identified. "
            f"Dispatching unit: {facility.name}, located at {facility.address}. "
            f"The unit is approximately {facility.distance_miles:.1f} miles away."
        )
    else:
        dispatch_info = f"We were unable to locate a nearby {msg.type.replace('_', ' ')} for dispatch. Please review manually."

    closing = "This concludes the alert. Goodbye."
    return f"{opening} {incident} {dispatch_info} {closing}"

def make_vapi_call(phone_number: str, message: str, ctx: Context) -> bool:
    """Initiates a phone call and returns True on success."""
    ctx.logger.info(f"Initiating call to {phone_number} via VAPI...")
    
    url = "https://api.vapi.ai/phone-call/send"
    headers = {"Authorization": f"Bearer {VAPI_AUTH_TOKEN}"}
    payload = {"assistantId": VAPI_ASSISTANT_ID, "phoneNumber": phone_number, "firstMessage": message}

    try:
        # response = requests.post(url, headers=headers, json=payload, timeout=10)
        response = requests.post("", headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        ctx.logger.info(f"VAPI call initiated successfully. Response: {response.json()}")
        return True
    except requests.exceptions.RequestException as e:
        ctx.logger.error(f"Failed to initiate VAPI call: {e}")
        return False

# --- Message Handler ---
@vapi_agent.on_message(model=DispatchedIncidentReport, replies=NotificationStatus)
async def handle_notification_request(ctx: Context, sender: str, msg: DispatchedIncidentReport):
    ctx.logger.info(f"Received notification request from {sender}.")
    
    summary_message = create_spoken_summary(msg)
    ctx.logger.info(f"Generated spoken message: \"{summary_message}\"")

    success = False
    if "your-vapi-auth-token" not in VAPI_AUTH_TOKEN:
        success = make_vapi_call(RECIPIENT_PHONE_NUMBER, summary_message, ctx)
    else:
        ctx.logger.warning("VAPI credentials are placeholders. Skipping phone call.")

    # Reply to the dispatcher with the status of the call
    status_message = "Notification sent successfully." if success else "Notification failed."
    await ctx.send(sender, NotificationStatus(success=success, message=status_message))


if __name__ == "__main__":
    vapi_agent.run()
