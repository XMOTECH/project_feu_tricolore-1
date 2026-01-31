from datetime import datetime
from database import DatabaseManager

class Logger:
    def __init__(self):
        self.db = DatabaseManager()
    
    def log_event(self, type_action, action, traffic_light, scenario_name, vehicle=None):
        """
        Enregistre un événement.
        - traffic_light: objet feu pour récupérer l'état
        - vehicle: objet voiture (optionnel) pour position/vitesse
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Récupération sécurisée des infos
        etat_feu = traffic_light.state if traffic_light else "N/A"
        
        # Gestion des données voiture (si présentes)
        if vehicle:
            id_voiture = str(vehicle.id)
            pos_x = f"{vehicle.x:.1f}"
            pos_y = f"{vehicle.y:.1f}"
            vitesse = f"{vehicle.current_speed:.1f}"
        else:
            id_voiture = "N/A"
            pos_x = "N/A"
            pos_y = "N/A"
            vitesse = "N/A"

        query = """
        INSERT INTO logs (timestamp, type_action, action, etat_feu, scenario, id_voiture, position_x, position_y, vitesse)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        params = (timestamp, type_action, action, etat_feu, scenario_name, id_voiture, pos_x, pos_y, vitesse)
        
        self.db.execute_query(query, params)
        print(f"[LOG] {action}") # Feedback console