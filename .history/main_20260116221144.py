import turtle
import time
from turtle_scene import SceneBuilder
from traffic_light import TrafficLight
from vehicles import Vehicle, VehicleManager
from gui import InterfaceManager
from scenarios import NormalScenario, RushHourScenario, NightScenario, ManualScenario
from logger import Logger  # <--- NOUVEL IMPORT

class SimulationController:
    def __init__(self):
        self.screen = turtle.Screen()
        self.screen.title("Simulation Feu Tricolore - Projet L3")
        self.screen.setup(width=800, height=600)
        self.screen.tracer(0)

        self.scene = SceneBuilder()
        self.gui = InterfaceManager()
        self.traffic_light = TrafficLight(0, 0)
        self.veh_manager = VehicleManager()
        
        # --- NOUVEAU : Logger ---
        self.logger = Logger()
        
        self.is_running = True
        self.is_paused = False 

        self.scene.draw_background()
        self.scene.draw_roads()
        self.gui.draw_controls()

        self.test_car = Vehicle(1, -350, -20)
        self.veh_manager.vehicles.append(self.test_car)

        self.scenarios = {
            "SCENARIO_1": NormalScenario(),
            "SCENARIO_2": RushHourScenario(),
            "SCENARIO_3": NightScenario(),
            "SCENARIO_4": ManualScenario()
        }
        self.current_scenario = self.scenarios["SCENARIO_1"]
        
        # Log du démarrage
        self.logger.log_event("SYSTEM", "Démarrage Application", self.traffic_light, self.current_scenario.name)

        self.screen.onclick(self.handle_mouse_click)

    def handle_mouse_click(self, x, y):
        action = self.gui.handle_click(x, y)
        
        if not action: return

        # Log de l'interaction utilisateur
        self.logger.log_event("USER_INPUT", f"Clic sur {action}", self.traffic_light, self.current_scenario.name)

        if action == "PAUSE":
            self.is_paused = True
        elif action == "PLAY":
            self.is_paused = False
        elif action == "STOP":
            self.is_running = False
            self.logger.log_event("SYSTEM", "Arrêt Application", self.traffic_light, self.current_scenario.name)
        elif action == "RESET":
            self.test_car.x = -350
            self.test_car.current_speed = self.test_car.max_speed
            self.traffic_light.state = "ROUGE"
            self.traffic_light.timer = 0
            self.traffic_light.update_visuals()
            self.is_paused = True
            self.logger.log_event("SYSTEM", "Réinitialisation", self.traffic_light, self.current_scenario.name, self.test_car)

        elif action in self.scenarios:
            self.current_scenario = self.scenarios[action]
            if self.traffic_light.state == "ETEINT": # Sécurité visuelle
                self.traffic_light.state = "ORANGE"
                self.traffic_light.update_visuals()
            # Log changement scénario
            self.logger.log_event("SCENARIO", f"Changement vers {self.current_scenario.name}", self.traffic_light, self.current_scenario.name)

        elif action == "MANUAL_CLICK":
            if isinstance(self.current_scenario, ManualScenario):
                self.traffic_light.manual_change()
                self.logger.log_event("TRAFFIC_LIGHT", f"Changement Manuel vers {self.traffic_light.state}", self.traffic_light, self.current_scenario.name)

    def run(self):
        # Pour détecter le changement automatique de feu
        previous_light_state = self.traffic_light.state

        while self.is_running:
            if not self.is_paused:
                self.traffic_light.update(self.current_scenario)
                self.veh_manager.update_vehicles(self.traffic_light)

                # Détection changement de feu (Automatique)
                if self.traffic_light.state != previous_light_state:
                    self.logger.log_event("TRAFFIC_LIGHT", f"Feu passé à {self.traffic_light.state}", self.traffic_light, self.current_scenario.name)
                    previous_light_state = self.traffic_light.state
            
            self.screen.update()
            time.sleep(0.02)

if __name__ == "__main__":
    app = SimulationController()
    app.run()