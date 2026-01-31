import sqlite3

class DatabaseManager:
    def __init__(self, db_name="traffic_sim.db"):
        self.db_name = db_name
        self.create_tables()

    def get_connection(self):
        return sqlite3.connect(self.db_name)

    def create_tables(self):
        """Crée la table de logs exactement comme demandé dans le PDF."""
        sql_create_logs = """
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            type_action TEXT,
            action TEXT,
            etat_feu TEXT,
            scenario TEXT,
            id_voiture TEXT,
            position_x TEXT,
            position_y TEXT,
            vitesse TEXT
        );
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(sql_create_logs)
                conn.commit()
        except Exception as e:
            print(f"[ERREUR DB] Création table: {e}")

    def execute_query(self, query, params=()):
        """Exécute une requête INSERT de manière sécurisée."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                conn.commit()
        except Exception as e:
            print(f"[ERREUR DB] Query: {e}")