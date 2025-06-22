from pydantic import BaseModel
from typing import Optional

class AmbulanceRequest(BaseModel):
    note: str
    lat: float
    lon: float
    request_id: str

class AmbulanceDispatchFinalResponse(BaseModel):
    type: str 
    name: str
    address: str
    distance: str
    lat: float
    lon: float