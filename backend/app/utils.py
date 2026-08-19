import json
import os
import logging
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import QTableEntry

logger = logging.getLogger("traffic_sim_backend")

async def import_legacy_q_table(db: AsyncSession):
    """Importe automatiquement la Q-table historique dans Postgres si elle est vide."""
    # Vérifier si la table a déjà des données
    query = select(QTableEntry).limit(1)
    result = await db.execute(query)
    if result.scalars().first() is not None:
        logger.info("La table Q dans la base de données contient déjà des données. Importation ignorée.")
        return

    # Chemin d'accès dans le conteneur Docker ou localement
    legacy_path = "/app/legacy_python/q_table.json"
    if not os.path.exists(legacy_path):
        # Fallback pour le dev local hors conteneur
        legacy_path = os.path.join(os.path.dirname(__file__), "../../legacy_python/q_table.json")

    if not os.path.exists(legacy_path):
        logger.warning(f"Fichier hérité q_table.json introuvable à la trajectoire : {legacy_path}")
        return

    logger.info(f"Fichier hérité q_table.json trouvé à : {legacy_path}. Importation en cours...")
    try:
        with open(legacy_path, 'r') as f:
            data = json.load(f)
        
        entries = []
        for key, vals in data.items():
            if len(vals) >= 2:
                entries.append(QTableEntry(
                    state_key=key,
                    action_stay=vals[0],
                    action_switch=vals[1]
                ))
        
        if entries:
            db.add_all(entries)
            await db.commit()
            logger.info(f"Importation réussie de {len(entries)} états de Q-table.")
    except Exception as e:
        logger.error(f"Erreur lors de l'importation de la Q-table héritée : {e}")
