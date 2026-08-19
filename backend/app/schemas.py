from pydantic import BaseModel
from typing import Optional, Dict, List

class TrafficLogBase(BaseModel):
    timestamp: str
    type_action: str
    action: str
    etat_feu: str
    scenario: str
    id_voiture: Optional[str] = "N/A"
    position_x: Optional[str] = "N/A"
    position_y: Optional[str] = "N/A"
    vitesse: Optional[str] = "N/A"

class TrafficLogCreate(TrafficLogBase):
    pass

class TrafficLogResponse(TrafficLogBase):
    id: int

    class Config:
        from_attributes = True

class QTableEntryBase(BaseModel):
    state_key: str
    action_stay: float
    action_switch: float

class QTableEntryCreate(QTableEntryBase):
    pass

class QTableEntryResponse(QTableEntryBase):
    class Config:
        from_attributes = True

class QTableBulkUpdate(BaseModel):
    entries: List[QTableEntryCreate]

class DQNWeightsBase(BaseModel):
    key: str
    weights_json: str

class DQNWeightsCreate(DQNWeightsBase):
    pass

class DQNWeightsResponse(DQNWeightsBase):
    class Config:
        from_attributes = True

