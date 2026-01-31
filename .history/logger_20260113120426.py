from datetime import datetime
from database import DatabaseManager

class Logger:
    def __init__(self):
        self.db = DatabaseManager()
    
    def log_event(self, action_type, details, traffic_state, scenario_name):
        """Enregistre un événement dans la base."""
        print(f"[LOG] {action_type}: {details}") # Pour debug console
        pass