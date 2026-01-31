import turtle
import time
from turtle_scene import SceneBuilder
from traffic_light import TrafficLight
from vehicles import Vehicle, VehicleManager
from gui import InterfaceManager
from scenarios import NormalScenario, RushHourScenario, NightScenario, ManualScenario

class SimulationController:
    def __init__(self):
        # 1. Configuration de la fenêtre
        self.screen = turtle.Screen()
        self.screen.title("Simulation Feu Tricolore - Projet L3")
        self.screen.setup(width=800, height=600)
        self.screen.tracer(0)

        # 2. Initialisation des modules
        self.scene = SceneBuilder()
        self.gui = InterfaceManager()
        self.traffic_light = TrafficLight(0, 0)
        self.veh_manager = VehicleManager()
        
        # 3. État de la simulation
        self.is_running = True
        self.is_paused = False 

        # 4. Dessin initial
        self.scene.draw_background()
        self.scene.draw_roads()
        self.gui.draw_controls()

        # 5. Voiture de test (Temporaire, pour vérifier l'animation)
        self.test_car = Vehicle(1, -350, -20)
        self.veh_manager.vehicles.append(self.test_car)

        # 6. Initialisation des scénarios
        self.scenarios = {
            "SCENARIO_1": NormalScenario(),
            "SCENARIO_2": RushHourScenario(),
            "SCENARIO_3": NightScenario(),
            "SCENARIO_4": ManualScenario()
        }
        self.current_scenario = self.scenarios["SCENARIO_1"] # Par défaut : Normal

        # 7. Activation de l'écoute souris
        self.screen.onclick(self.handle_mouse_click)


    def handle_mouse_click(self, x, y):
        """Gestion centralisée des clics."""
        action = self.gui.handle_click(x, y)
        
        # --- Gestion des boutons de lecture ---
        if action == "PAUSE":
            self.is_paused = True
            print("Simulation en PAUSE")
        elif action == "PLAY":
            self.is_paused = False
            print("Simulation en LECTURE")
        elif action == "STOP":
            self.is_running = False
            print("Arrêt du programme...")
        elif action == "RESET":
            self.test_car.x = -350
            self.test_car.current_speed = self.test_car.max_speed
            self.traffic_light.state = "ROUGE"
            self.traffic_light.timer = 0
            self.traffic_light.update_visuals()
            self.is_paused = True
            print("Simulation réinitialisée")

        # --- Gestion des Scénarios ---
        elif action in self.scenarios:
            self.current_scenario = self.scenarios[action]
            print(f"Scénario activé : {self.current_scenario.name}")
            
            # Petit nettoyage visuel si on quitte le mode nuit
            if self.traffic_light.state == "ETEINT":
                self.traffic_light.state = "ORANGE"
                self.traffic_light.update_visuals()

        # --- Gestion du Mode Manuel ---
        elif action == "MANUAL_CLICK":
            # On ne change le feu manuellement que si on est dans le scénario manuel
            if isinstance(self.current_scenario, ManualScenario):
                self.traffic_light.manual_change()
                print("Changement manuel du feu")
            else:
                print("Erreur: Activez d'abord le Scénario 4 (Manuel)")


    def run(self):
        """Boucle principale."""
        while self.is_running:
            if not self.is_paused:
                # 1. Le feu se met à jour selon la STRATÉGIE actuelle
                # IMPORTANT: On passe 'current_scenario' en argument !
                self.traffic_light.update(self.current_scenario)
                
                # 2. Les voitures avancent et vérifient le feu
                self.veh_manager.update_vehicles(self.traffic_light)
            
            self.screen.update()
            time.sleep(0.02)

if __name__ == "__main__":
    app = SimulationController()
    app.run()