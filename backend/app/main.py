from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert as pg_insert
from contextlib import asynccontextmanager
from typing import Dict, List
import logging

from app.database import engine, Base, get_db, AsyncSessionLocal
from app.models import TrafficLog, QTableEntry, DQNWeights
from app.schemas import TrafficLogCreate, TrafficLogResponse, DQNWeightsCreate, DQNWeightsResponse
from app.utils import import_legacy_q_table

# Logger config
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("traffic_sim_backend")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialisation de la base de données (création des tables)
    logger.info("Démarrage de l'application, création des tables dans PostgreSQL...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    # Importation automatique de la Q-table héritée
    async with AsyncSessionLocal() as session:
        await import_legacy_q_table(session)
        
    yield
    logger.info("Arrêt de l'application...")

app = FastAPI(
    title="Traffic Light Simulation Backend",
    description="Backend de gestion des logs et de la Q-Table pour le simulateur de carrefour",
    version="1.0.0",
    lifespan=lifespan
)

# Configuration CORS pour permettre au frontend React de communiquer
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # En développement, on autorise tout. On pourra restreindre en production.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- ROUTES DES LOGS ---

@app.post("/api/logs", response_model=TrafficLogResponse, status_code=status.HTTP_201_CREATED)
async def create_log(log_in: TrafficLogCreate, db: AsyncSession = Depends(get_db)):
    """Enregistre un événement de simulation."""
    new_log = TrafficLog(**log_in.model_dump())
    db.add(new_log)
    await db.commit()
    await db.refresh(new_log)
    return new_log

@app.get("/api/logs", response_model=List[TrafficLogResponse])
async def get_logs(limit: int = 100, offset: int = 0, db: AsyncSession = Depends(get_db)):
    """Récupère les derniers logs de simulation."""
    query = select(TrafficLog).order_by(TrafficLog.id.desc()).offset(offset).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()

@app.delete("/api/logs/clear", status_code=status.HTTP_204_NO_CONTENT)
async def clear_logs(db: AsyncSession = Depends(get_db)):
    """Vide la table de logs."""
    await db.execute(Base.metadata.tables["traffic_logs"].delete())
    await db.commit()
    return None

# --- ROUTES DE LA Q-TABLE ---

@app.get("/api/q-table", response_model=Dict[str, List[float]])
async def get_q_table(db: AsyncSession = Depends(get_db)):
    """
    Récupère la Q-Table complète sous forme de dictionnaire compatible avec le format d'origine :
    { "state_key": [action_stay_val, action_switch_val] }
    """
    query = select(QTableEntry)
    result = await db.execute(query)
    entries = result.scalars().all()
    
    # Reconstruire le dictionnaire
    q_table_dict = {
        entry.state_key: [entry.action_stay, entry.action_switch]
        for entry in entries
    }
    return q_table_dict

@app.post("/api/q-table/bulk", status_code=status.HTTP_200_OK)
async def save_q_table_bulk(q_table_data: Dict[str, List[float]], db: AsyncSession = Depends(get_db)):
    """
    Enregistre ou met à jour la Q-Table en masse.
    Prend le format JSON original d'un dictionnaire : { "state_key": [stay, switch] }
    """
    if not q_table_data:
        return {"message": "Aucune donnée à sauvegarder"}

    values_list = []
    for key, vals in q_table_data.items():
        if len(vals) >= 2:
            values_list.append({
                "state_key": key,
                "action_stay": vals[0],
                "action_switch": vals[1]
            })

    if not values_list:
        raise HTTPException(status_code=400, detail="Format de données invalide")

    # Division par paquets pour éviter de saturer la mémoire/requête si la table est gigantesque
    chunk_size = 1000
    for i in range(0, len(values_list), chunk_size):
        chunk = values_list[i:i + chunk_size]
        
        # Requête native PostgreSQL ON CONFLICT DO UPDATE (Upsert)
        stmt = pg_insert(QTableEntry).values(chunk)
        stmt = stmt.on_conflict_do_update(
            index_elements=[QTableEntry.state_key],
            set_={
                'action_stay': stmt.excluded.action_stay,
                'action_switch': stmt.excluded.action_switch
            }
        )
        await db.execute(stmt)
    
    await db.commit()
    return {"message": f"Mise à jour réussie de {len(values_list)} états."}

@app.delete("/api/q-table/clear", status_code=status.HTTP_204_NO_CONTENT)
async def clear_q_table(db: AsyncSession = Depends(get_db)):
    """Réinitialise la Q-table en vidant les entrées."""
    await db.execute(Base.metadata.tables["q_table"].delete())
    await db.commit()
    return None

# --- ROUTES DU DQN ---

@app.get("/api/dqn-weights", response_model=DQNWeightsResponse)
async def get_dqn_weights(db: AsyncSession = Depends(get_db)):
    """Récupère les poids du DQN pour la clé 'latest'."""
    query = select(DQNWeights).where(DQNWeights.key == "latest")
    result = await db.execute(query)
    weights = result.scalars().first()
    if weights is None:
        raise HTTPException(status_code=404, detail="Aucun poids DQN trouvé")
    return weights

@app.post("/api/dqn-weights", response_model=DQNWeightsResponse)
async def save_dqn_weights(weights_in: DQNWeightsCreate, db: AsyncSession = Depends(get_db)):
    """Enregistre ou met à jour les poids du DQN (upsert)."""
    stmt = pg_insert(DQNWeights).values(
        key=weights_in.key,
        weights_json=weights_in.weights_json
    )
    stmt = stmt.on_conflict_do_update(
        index_elements=[DQNWeights.key],
        set_={'weights_json': stmt.excluded.weights_json}
    )
    await db.execute(stmt)
    await db.commit()
    
    # Récupérer l'enregistrement mis à jour
    query = select(DQNWeights).where(DQNWeights.key == weights_in.key)
    result = await db.execute(query)
    return result.scalars().first()

@app.delete("/api/dqn-weights/clear", status_code=status.HTTP_204_NO_CONTENT)
async def clear_dqn_weights(db: AsyncSession = Depends(get_db)):
    """Supprime les poids DQN sauvegardés."""
    await db.execute(Base.metadata.tables["dqn_weights"].delete())
    await db.commit()
    return None

