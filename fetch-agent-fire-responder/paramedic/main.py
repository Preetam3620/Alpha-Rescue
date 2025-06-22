# main.py
import asyncio
from uagents import Agent, Bureau, Context
from messages import AmbulanceRequest
from ambulance_agent import ambulance_agent

# Create a test sender agent
sender = Agent(name="test_sender",
    seed="test_sender_seed",
    port=8010,
    endpoint="http://127.0.0.1:8010/submit",)

@sender.on_event("startup")
async def send_request(ctx: Context):
    request = AmbulanceRequest(
        request_id="test-001",
        note="A person collapsed and is unconscious, possibly a heart issue.",
        lat=37.8715,
        lon=-122.2730
    )
    
    await ctx.send(ambulance_agent.address, request)

# Set up Bureau and run
bureau = Bureau()
bureau.add(sender)
bureau.add(ambulance_agent)

if __name__ == "__main__":
    bureau.run()
