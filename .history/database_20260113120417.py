import sqlite3

class DatabaseManager:
    def __init__(self, db_name="traffic_sim.db"):
        self.db_name = db_name
        self.connection = None

    def connect(self):
        """Établit la connexion à la BDD."""
        pass

    def create_tables(self):
        """Crée la table de logs si elle n'existe pas."""
        pass

    def execute_query(self, query, params=()):
        """Exécute une requête SQL."""
        pass