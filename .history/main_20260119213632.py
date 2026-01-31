import turtle
import time
from turtle_scene import SceneBuilder
from traffic_light import TrafficLight
from vehicles import Vehicle, VehicleManager
from gui import InterfaceManager
from scenarios import NormalScenario, RushHourScenario, NightScenario, ManualScenario
from logger import Logger

class SimulationController:
    def __init__(self):
        # 1. Setup écran
        self.screen = turtle.Screen()
        self.screen.title("Simulation Carrefour Réaliste (4 Feux)")
        self.screen.setup(width=800, height=600)
        self.screen.tracer(0)

        # 2. Infrastructure
        self.scene = SceneBuilder()
        self.gui = InterfaceManager()
        self.logger = Logger()
        
        # 3. Création des 4 Feux (Positionnement aux coins)
        # Nord et Sud (Axe Vertical)
        self.light_N = TrafficLight(-90, 180)
        self.light_S = TrafficLight(90, -180)
        
        # Est et Ouest (Axe Horizontal)
        self.light_E = TrafficLight(180, 90)
        self.light_W = TrafficLight(-180, -90)

        # Dictionnaire pour le Scénario
        self.lights_dict = {
            'NS': [self.light_N, self.light_S],
            'EW': [self.light_E, self.light_W]
        }

        self.veh_manager = VehicleManager()
        self.is_running = True
        self.is_paused = False 

        # 4. Initialisation Scène
        self.scene.draw_background()
        self.scene.draw_roads()
        self.gui.draw_controls()

        # Voiture de test (Attention: elle ne respecte pas encore les 4 feux !)
        self.test_car = Vehicle(1, -350, -20)
        self.veh_manager.vehicles.append(self.test_car)

        # 5. Scénarios
        self.scenarios = {
            "SCENARIO_1": NormalScenario(),
            "SCENARIO_2": RushHourScenario(),
            "SCENARIO_3": NightScenario(),
            "SCENARIO_4": ManualScenario()
        }
        self.current_scenario = self.scenarios["SCENARIO_1"]
        
        self.logger.log_event("SYSTEM", "Démarrage V2 Réaliste", None, self.current_scenario.name)
        self.screen.onclick(self.handle_mouse_click)

    def handle_mouse_click(self, x, y):
        action = self.gui.handle_click(x, y)
        if not action: return

        if action == "PAUSE":
            self.is_paused = True
        elif action == "PLAY":
            self.is_paused = False
        elif action == "STOP":
            self.is_running = False
        elif action == "RESET":
            # Reset simple pour l'instant
            self.test_car.x = -350
            self.is_paused = True
            
        elif action in self.scenarios:
            self.current_scenario = self.scenarios[action]
            print(f"Scénario activé : {self.current_scenario.name}")

        elif action == "MANUAL_CLICK":
            if isinstance(self.current_scenario, ManualScenario):
                self.current_scenario.switch_phase(self.lights_dict)
                print("Changement de phase manuel")

    def run(self):
        while self.is_running:
            if not self.is_paused:
                # MISE A JOUR DES FEUX (Nouvelle méthode avec dict)
                self.current_scenario.update_lights(self.lights_dict)
                
                # MISE A JOUR VOITURES (Logique temporaire pour éviter crash)
                # On passe juste un feu "par défaut" pour que ça ne plante pas
                # La vraie intelligence voiture arrive à l'étape suivante
                self.veh_manager.update_vehicles(self.light_W)
            
            self.screen.update()
            time.sleep(0.02)

if __name__ == "__main__":
    app = SimulationController()
    app.run()