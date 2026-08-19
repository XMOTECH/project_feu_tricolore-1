from sqlalchemy import Column, Integer, String, Float
from app.database import Base

class TrafficLog(Base):
    __tablename__ = "traffic_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(String, nullable=False)
    type_action = Column(String, nullable=False) # e.g. SYSTEM, USER_INPUT, SCENARIO, VEHICLE, TRAFFIC_LIGHT
    action = Column(String, nullable=False)      # e.g. Démarrage, Clic sur PLAY, etc.
    etat_feu = Column(String, nullable=False)    # e.g. ROUGE, VERT, ORANGE, A, B, etc.
    scenario = Column(String, nullable=False)    # e.g. Normal, Heure de Pointe, etc.
    id_voiture = Column(String, default="N/A")
    position_x = Column(String, default="N/A")
    position_y = Column(String, default="N/A")
    vitesse = Column(String, default="N/A")

class QTableEntry(Base):
    __tablename__ = "q_table"

    state_key = Column(String, primary_key=True, index=True)
    action_stay = Column(Float, default=0.0)    # Action 0 : Rester dans la même phase
    action_switch = Column(Float, default=0.0)  # Action 1 : Changer de phase

class DQNWeights(Base):
    __tablename__ = "dqn_weights"

    key = Column(String, primary_key=True, index=True) # e.g., "latest"
    weights_json = Column(String, nullable=False)       # Serialized weights and biases in JSON format

